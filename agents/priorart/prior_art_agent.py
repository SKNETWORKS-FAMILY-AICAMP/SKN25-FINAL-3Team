"""
선행기술조사 에이전트
- S3 XML → RDS pgvector 기반 임베딩 유사도 검색
- invention_payload JSON → 쿼리 추출 → pgvector Top-N 검색 → 근거문장 + 리스크 분석
"""

import time
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import Text

from agents.priorart.patent_db import PatentCorpus, SessionLocal

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBED_MODEL   = "text-embedding-3-small"
ANALYZE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANALYZE_MAX_WORKERS = int(os.getenv("PRIOR_ART_ANALYZE_MAX_WORKERS", "5"))


# ─────────────────────────────────────────────────────────────
# 1. 임베딩 유틸
# ─────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> np.ndarray:
    """OpenAI 임베딩 API 배치 호출 (load_corpus.py에서도 재사용)"""
    batch_size = 100
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vecs = [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
        all_vecs.extend(vecs)
    return np.array(all_vecs, dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 2. Payload → 검색 쿼리 텍스트 추출
# ─────────────────────────────────────────────────────────────

def _build_query_text(invention_payload: dict) -> str:
    # 청구항 초안이 있으면 최우선 사용
    # 코퍼스의 claim1과 같은 성격의 텍스트끼리 비교 → 임베딩 공간에서 더 정확한 매칭
    draft_claim1 = invention_payload.get("draft_claim1", "")
    if draft_claim1:
        return draft_claim1

    consulting = invention_payload.get("db_payload", {}).get("consulting", {})
    parts = []
    if consulting.get("summary_problem"):
        parts.append(f"문제: {consulting['summary_problem']}")
    if consulting.get("summary_solution"):
        parts.append(f"해결책: {consulting['summary_solution']}")
    if consulting.get("summary_difference"):
        parts.append(f"차별점: {consulting['summary_difference']}")
    return " ".join(parts)


# ─────────────────────────────────────────────────────────────
# 3. pgvector 기반 Top-N 검색
# ─────────────────────────────────────────────────────────────

def search_similar_patents(
    query_text: str,
    top_n: int = 5,
    ipc_prefix: str = None,
) -> list[dict]:
    embed_started_at = time.perf_counter()
    query_vec = embed_texts([query_text])[0].tolist()
    print(f"[선행기술조사] 쿼리 임베딩 소요: {time.perf_counter() - embed_started_at:.2f}초")

    db = SessionLocal()
    try:
        search_started_at = time.perf_counter()
        # 거리값을 결과와 함께 가져오기 위해 label로 추가
        # 이렇게 해야 각 결과별 similarity_score를 정확히 계산 가능
        distance_col = PatentCorpus.embedding.cosine_distance(query_vec).label("distance")

        q = db.query(PatentCorpus, distance_col)

        # IPC 필터: 기술 분야가 명확하면 관련 없는 특허 미리 제거
        if ipc_prefix:
            q = q.filter(
                PatentCorpus.ipc_codes.cast(Text).like(f"%{ipc_prefix}%")
            )

        rows = q.order_by(distance_col).limit(top_n).all()
        print(f"[선행기술조사] DB 유사도 검색 소요: {time.perf_counter() - search_started_at:.2f}초")

        return [
            {
                "patent_number":  row.PatentCorpus.application_number,
                "title":          row.PatentCorpus.title,
                "applicant":      row.PatentCorpus.applicant,
                "abstract":       row.PatentCorpus.abstract,
                "claims":         row.PatentCorpus.claim1,
                "ipc_codes":      row.PatentCorpus.ipc_codes,
                "examiner_cited": row.PatentCorpus.examiner_cited,
                # cosine_distance 범위 0~2 → 1 - distance/2 로 0~1 유사도 변환
                "similarity_score": round(1 - float(row.distance) / 2, 4),
            }
            for row in rows
        ]
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# 4. LLM 기반 근거 문장 + 리스크 분석
# ─────────────────────────────────────────────────────────────

def _analyze_patent(invention_payload: dict, patent: dict) -> dict:
    consulting = invention_payload.get("db_payload", {}).get("consulting", {})
    steps = invention_payload.get("db_payload", {}).get("algorithm_steps", [])
    steps_text = "\n".join(
        f"  {s['step_seq']}. {s['step_content']}" for s in steps
    )

    patent_body = "\n".join(filter(None, [
        f"제목: {patent.get('title', '')}",
        f"출원번호: {patent.get('patent_number', '')}",
        f"요약: {patent.get('abstract', '')}",
        f"청구항: {patent.get('claims', '')}",
    ]))

    prompt = f"""당신은 대한민국 특허법 전문 변리사입니다.
아래 [발명]과 [선행특허]를 비교하여 신규성·진보성 침해 리스크를 분석하세요.

─── 발명 ───
문제점: {consulting.get('summary_problem', '')}
해결책: {consulting.get('summary_solution', '')}
차별점: {consulting.get('summary_difference', '')}
기대효과: {consulting.get('summary_effect', '')}
알고리즘:
{steps_text}

─── 선행특허 ───
{patent_body[:2500]}

─── 지침 ───
1. 발명과 선행특허에서 실제로 겹치는 구절·개념을 근거문장으로 추출하세요.
2. 추측하지 말고 텍스트에 명시된 내용만 사용하세요.
3. risk_level: high(신규성 부정 가능), medium(진보성 위협), low(영향 미미)

반드시 아래 JSON만 출력하세요:
{{
  "summary": "선행특허 핵심 요약",
  "overlap_points": ["본 발명과 겹치는 점"],
  "difference_points": ["본 발명과 다른 점"],
  "limitations": ["선행기술 또는 종래기술의 한계"],
  "evidence_sentences": [
    {{
      "patent_text": "선행특허의 근거 구절",
      "invention_text": "본 발명의 대응 내용",
      "overlap_type": "동일|유사|관련"
    }}
  ],
  "risk_level": "high|medium|low",
  "risk_reasons": ["리스크 이유"],
  "recommendation": "대응 전략"
}}"""

    resp = client.chat.completions.create(
        model=ANALYZE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_completion_tokens=3000,
    )
    return json.loads(resp.choices[0].message.content)


# ─────────────────────────────────────────────────────────────
# 5. 전체 리스크 요약
# ─────────────────────────────────────────────────────────────

def _summarize_overall_risk(results: list[dict]) -> dict:
    high   = sum(1 for r in results if r.get("risk_level") == "high")
    medium = sum(1 for r in results if r.get("risk_level") == "medium")
    low    = sum(1 for r in results if r.get("risk_level") == "low")

    if high >= 2:
        level = "high"
        summary = f"고위험 선행특허 {high}건 발견 — 청구항 범위 조정 및 회피설계 필요"
    elif high == 1 or medium >= 2:
        level = "medium"
        summary = f"주의 필요 선행특허 {high + medium}건 — 차별점 강조 및 청구항 보완 권장"
    else:
        level = "low"
        summary = "주요 저촉 선행기술 미발견 — 현재 방향으로 출원 진행 가능"

    return {
        "level": level,
        "summary": summary,
        "counts": {"high": high, "medium": medium, "low": low},
    }


def _merge_unique(groups: list[list[str]]) -> list[str]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            if item and item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


# ─────────────────────────────────────────────────────────────
# 6. 메인 에이전트 함수
# ─────────────────────────────────────────────────────────────

def run_prior_art_agent(
    invention_payload: dict,
    top_n: int = 5,
) -> dict:
    total_started_at = time.perf_counter()
    query_text = _build_query_text(invention_payload)
    print(f"[선행기술조사] 검색 쿼리:\n  {query_text[:200]}...")

    search_total_started_at = time.perf_counter()
    top_patents = search_similar_patents(query_text, top_n=top_n)
    print(f"[선행기술조사] 검색 전체 소요: {time.perf_counter() - search_total_started_at:.2f}초")

    if not top_patents:
        return {
            "error": "DB에 특허 데이터가 없습니다. load_corpus.py를 먼저 실행하세요.",
            "prior_art_results": [],
            "overall_risk": {"level": "unknown", "summary": "코퍼스 없음"},
        }

    print(f"[선행기술조사] 유사 특허 Top-{top_n} 선정 완료")

    def _analyze_one(index: int, patent: dict) -> tuple[int, dict, dict]:
        print(f"[선행기술조사] 분석 시작 {index+1}/{len(top_patents)}: {patent.get('title', '')[:50]}")
        analyze_started_at = time.perf_counter()
        try:
            analysis = _analyze_patent(invention_payload, patent)
        except Exception as e:
            analysis = {
                "summary": "",
                "overlap_points": [],
                "difference_points": [],
                "limitations": [],
                "evidence_sentences": [],
                "risk_level": "unknown",
                "risk_reasons": [f"분석 실패: {str(e)}"],
                "recommendation": "",
            }
        print(f"[선행기술조사] 분석 {index+1}/{len(top_patents)} 소요: {time.perf_counter() - analyze_started_at:.2f}초")
        return index, patent, analysis

    max_workers = max(1, min(ANALYZE_MAX_WORKERS, len(top_patents)))
    print(f"[선행기술조사] 후보 분석 병렬 실행: workers={max_workers}")

    analysis_items = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_analyze_one, i, patent)
            for i, patent in enumerate(top_patents)
        ]
        for future in as_completed(futures):
            analysis_items.append(future.result())

    analysis_items.sort(key=lambda item: item[0])

    candidates = []
    prior_art_results = []
    for i, patent, analysis in analysis_items:

        overlap_points    = analysis.get("overlap_points", [])
        difference_points = analysis.get("difference_points", [])
        limitations       = analysis.get("limitations", [])
        evidence_sentences = analysis.get("evidence_sentences", [])

        candidates.append({
            "patent_id":        patent.get("patent_number", ""),
            "publication_no":   patent.get("patent_number", ""),
            "title":            patent.get("title", ""),
            "summary":          analysis.get("summary", ""),
            "score":            patent.get("similarity_score", 0.0),
            "overlap_points":   overlap_points,
            "difference_points": difference_points,
            "limitations":      limitations,
            "evidence": [
                e.get("patent_text", "")
                for e in evidence_sentences
                if isinstance(e, dict) and e.get("patent_text")
            ],
            "pdf_path": None,
        })

        prior_art_results.append({
            "rank":             i + 1,
            "patent_number":    patent.get("patent_number", ""),
            "title":            patent.get("title", ""),
            "applicant":        patent.get("applicant", ""),
            "similarity_score": patent.get("similarity_score", 0.0),
            "differentiating_points": difference_points,
            **analysis,
        })

    overall_risk = _summarize_overall_risk(prior_art_results)
    print(f"\n[선행기술조사] 완료 — 전체 리스크: {overall_risk['level'].upper()}")
    print(f"[선행기술조사] 전체 실행 소요: {time.perf_counter() - total_started_at:.2f}초")

    overlap_points    = _merge_unique([c["overlap_points"] for c in candidates])
    difference_points = _merge_unique([c["difference_points"] for c in candidates])
    limitations       = _merge_unique([c["limitations"] for c in candidates])

    analysis_summary = " ".join(filter(None, [
        f"종래기술은 {overlap_points[0]} 측면에서 관련성이 있습니다." if overlap_points else "",
        f"다만 {limitations[0]} 한계가 있습니다." if limitations else "",
        f"본 발명은 {difference_points[0]} 점에서 차별화됩니다." if difference_points else "",
    ])) or overall_risk["summary"]

    return {
        "status":             "ok",
        "summary":            overall_risk["summary"],
        "warnings":           [],
        "notes":              [],
        "query":              query_text,
        "ipc_focus":          [],
        "candidates":         candidates,
        "analysis_summary":   analysis_summary,
        "overlap_points":     overlap_points,
        "difference_points":  difference_points,
        "limitations":        limitations,
        "novelty_risk":       overall_risk["level"],
        "inventive_step_risk": overall_risk["level"],
        "details": {
            "corpus_size": len(top_patents),
            "overall_risk": overall_risk,
        },
    }


# ─────────────────────────────────────────────────────────────
# CLI 실행 (테스트용)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    sample_payload = {
        "db_payload": {
            "consulting": {
                "summary_problem": "온라인 플랫폼에서 유사한 댓글이 반복 노출되어 사용자가 핵심 의견을 파악하기 어렵다",
                "summary_solution": "자연어 임베딩으로 댓글을 벡터화하고 의미 유사도 기반 클러스터링 후 생성형 AI로 대표 통합 댓글을 생성한다",
                "summary_difference": "기존 추천 수/시간순 정렬과 달리 의미 기반 그룹화와 생성형 AI 요약을 결합한다",
                "summary_effect": "방대한 댓글을 읽지 않고도 전체 의견 흐름을 직관적으로 파악할 수 있다",
            },
            "algorithm_steps": [
                {"step_seq": 1, "step_content": "댓글 수집 및 저장"},
                {"step_seq": 2, "step_content": "자연어 임베딩으로 벡터 변환"},
                {"step_seq": 3, "step_content": "코사인 유사도 기반 클러스터링"},
                {"step_seq": 4, "step_content": "생성형 AI로 대표 댓글 생성"},
                {"step_seq": 5, "step_content": "고유 작성자 수 기준 정렬 및 표시"},
            ],
        },
        "extended_info": {"overall_flow": {"value": ""}},
    }

    payload_path = sys.argv[1] if len(sys.argv) > 1 else None
    if payload_path and os.path.exists(payload_path):
        with open(payload_path, encoding="utf-8") as f:
            sample_payload = json.load(f)

    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    result = run_prior_art_agent(sample_payload, top_n=top_n)
    print("\n" + "=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
