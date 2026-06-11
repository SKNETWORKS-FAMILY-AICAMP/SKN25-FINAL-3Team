"""
선행기술조사 에이전트
- S3 XML → RDS pgvector 기반 임베딩 유사도 검색
- PatentState.claims_data → 쿼리 추출 → pgvector Top-N 검색 → 근거문장 + 리스크 분석
"""

import time
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import Text, text
from agents.core.state import (
    ClaimResult,
    PatentState,
    PriorArtCandidate,
    PriorArtResult,
)
from agents.prior_art_agent.patent_db import PatentCorpus, SessionLocal

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
# 2. ClaimResult → 청구항 1 검색 쿼리 텍스트 추출
# ─────────────────────────────────────────────────────────────

def _build_claim1_query_text(claims_data: ClaimResult) -> str:
    claim1 = next(
        (claim for claim in claims_data.claims if claim.claim_no == 1),
        None,
    )
    
    if claim1 is None or not claim1.content:
        return ""
    
    return claim1.content.strip()
    

# ─────────────────────────────────────────────────────────────
# 3. pgvector 기반 Top-N 검색
# ─────────────────────────────────────────────────────────────

def search_similar_patents(
    query_text: str,
    top_n: int = 5,
    ipc_prefix: str = None,
    bm25_pool: int = 500,
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

        trgm_query = query_text[:500]
        pre_filter_sql = text("""
            SELECT id FROM patent_corpus
            WHERE (title || ' ' || abstract || ' ' || claim1) % :q
                OR similarity(title || ' ' || abstract || ' ' || claim1, :q) > 0.05
            ORDER BY similarity(title || ' ' || abstract || ' ' || claim1, :q) DESC
            LIMIT :limit
        """)
        pre_ids = [
            row[0]
            for row in db.execute(pre_filter_sql, {"q": trgm_query, "limit": bm25_pool})
        ]
        print(f"[선행기술조사] trigram 후보 {len(pre_ids)}건 필터링")


        q = db.query(PatentCorpus, distance_col)

        if pre_ids:
            q = q.filter(PatentCorpus.id.in_(pre_ids))

        # IPC 필터: 기술 분야가 명확하면 관련 없는 특허 미리 제거
        if ipc_prefix:
            q = q.filter(
                PatentCorpus.ipc_codes.cast(Text).like(f"%{ipc_prefix}%")
            )

        rows = q.order_by(distance_col).limit(top_n).all()
        print(f"[선행기술조사] DB 유사도 검색 소요: {time.perf_counter() - search_started_at:.2f}초")

        return [
            {
                "patent_id":  row.PatentCorpus.id,
                "register_number": row.PatentCorpus.register_number,
                "title":          row.PatentCorpus.title,
                "applicant":      row.PatentCorpus.applicant,
                "abstract":       row.PatentCorpus.abstract,
                "claims":         row.PatentCorpus.claim1,
                "ipc_codes":      row.PatentCorpus.ipc_codes,
                "examiner_cited": row.PatentCorpus.examiner_cited,
                "pdf_s3_url":     row.PatentCorpus.pdf_s3_url,
                "similarity_score": round(1 - float(row.distance) / 2, 4),
            }
            for row in rows
        ]
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# 4. LLM 기반 근거 문장 + 리스크 분석
# ─────────────────────────────────────────────────────────────

def _analyze_patent(claims_data: ClaimResult, patent: dict) -> dict:
    claim1_text = _build_claim1_query_text(claims_data)

    patent_body = "\n".join(filter(None, [
        f"제목: {patent.get('title', '')}",
        f"출원번호: {patent.get('register_number', '')}",
        f"선행특허 청구항 1: {patent.get('claims', '')}",
        f"요약: {patent.get('abstract', '')}",
    ]))

    prompt = f"""당신은 대한민국 특허법 전문 변리사입니다.
아래 [본원 청구항]과 [선행특허]를 비교하여 신규성·진보성 거절 리스크를 분석하세요.

─── 본원 청구항 1 ───
{claim1_text}

─── 선행특허 ───
{patent_body[:2500]}

─── 지침 ───
1. 본원 청구항 1과 선행특허 청구항 1에서 실제로 겹치는 구성요소, 동작, 효과를 근거문장으로 추출하세요.
2. 청구항 문언 기준으로 판단하세요.
3. 추측하지 말고 텍스트에 명시된 내용만 사용하세요.
4. risk_level: high(본원 청구항의 핵심 구성이 대부분 개시됨), medium(일부 핵심 구성이 유사함), low(관련성 낮음)

반드시 아래 JSON만 출력하세요:
{{
  "summary": "선행특허 핵심 요약",
  "overlap_points": ["본원 청구항 1과 겹치는 점"],
  "difference_points": ["본원 청구항 1과 다른 점"],
  "limitations": ["선행기술 또는 종래기술의 한계"],
  "evidence_sentences": [
    {{
      "patent_text": "선행특허의 근거 구절",
      "invention_text": "본원 청구항 1의 대응 내용",
      "overlap_type": "동일|유사|관련"
    }}
  ],
  "risk_level": "high|medium|low",
  "risk_reasons": ["리스크 이유"],
  "recommendation": "본원 청구항 보정 또는 대응 전략"
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
    #같은 문장 중복 X
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
    state: PatentState,
    top_n: int = 5,
) -> dict:
    total_started_at = time.perf_counter()
    claims_data = state.get("claims_data")
    if claims_data is None or not claims_data.claims:
        return {"prior_art_data": PriorArtResult(candidates=[])}

    query_text = _build_claim1_query_text(claims_data)
    if not query_text:
        return {"prior_art_data": PriorArtResult(candidates=[])}

    print(f"[선행기술조사] 청구항 1 검색 쿼리:\n  {query_text[:200]}...")

    search_total_started_at = time.perf_counter()
    top_patents = search_similar_patents(query_text, top_n=top_n)
    print(f"[선행기술조사] 검색 전체 소요: {time.perf_counter() - search_total_started_at:.2f}초")

    if not top_patents:
        return {
           "prior_art_data": PriorArtResult(candidates=[])
        }

    print(f"[선행기술조사] 유사 특허 Top-{top_n} 선정 완료")

    def _analyze_one(index: int, patent: dict) -> tuple[int, dict, dict]:
        print(f"[선행기술조사] 분석 시작 {index+1}/{len(top_patents)}: {patent.get('title', '')[:50]}")
        analyze_started_at = time.perf_counter()
        try:
            analysis = _analyze_patent(claims_data, patent)
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

        candidates.append(
            PriorArtCandidate(
                patent_id=patent["patent_id"],
                rank=i + 1,
                register_number=patent.get("register_number", ""),
                title=patent.get("title", ""),
                summary=analysis.get("summary", ""),
                score=patent.get("similarity_score", 0.0),
                overlap_points=overlap_points,
                difference_points=difference_points,
                limitations=limitations,
                evidence=[
                    evidence.get("patent_text", "")
                    for evidence in evidence_sentences
                    if isinstance(evidence, dict) and evidence.get("patent_text")
                ],
                risk_level=analysis.get("risk_level", "unknown"),
                risk_reasons=analysis.get("risk_reasons", []),
                recommendation=analysis.get("recommendation", ""),
                pdf_s3_url=patent.get("pdf_s3_url"),
            )
        )

        prior_art_results.append({
            "rank":             i + 1,
            "register_number":    patent.get("register_number", ""),
            "title":            patent.get("title", ""),
            "applicant":        patent.get("applicant", ""),
            "similarity_score": patent.get("similarity_score", 0.0),
            "differentiating_points": difference_points,
            **analysis,
        })

    overall_risk = _summarize_overall_risk(prior_art_results)
    print(f"\n[선행기술조사] 완료 — 전체 리스크: {overall_risk['level'].upper()}")
    print(f"[선행기술조사] 전체 실행 소요: {time.perf_counter() - total_started_at:.2f}초")

    overlap_points = _merge_unique([c.overlap_points for c in candidates])
    difference_points = _merge_unique([c.difference_points for c in candidates])
    limitations = _merge_unique([c.limitations for c in candidates])
    
    analysis_summary = " ".join(filter(None, [
        f"종래기술은 {overlap_points[0]} 측면에서 관련성이 있습니다." if overlap_points else "",
        f"다만 {limitations[0]} 한계가 있습니다." if limitations else "",
        f"본 발명은 {difference_points[0]} 점에서 차별화됩니다." if difference_points else "",
    ])) or overall_risk["summary"]

    return {
        "prior_art_data": PriorArtResult(
            candidates=candidates,
            overall_risk=overall_risk,
            analysis_summary=analysis_summary,
        )
    }


# ─────────────────────────────────────────────────────────────
# CLI 실행 (테스트용)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    sample_claims = {
        "claims": [
            {
                "claim_no": 1,
                "is_dependent": False,
                "cited_claim_no": [],
                "category": "시스템",
                "content": (
                    "복수의 사용자 댓글을 입력받는 입력부; 상기 복수의 사용자 댓글 각각을 "
                    "의미 벡터로 변환하는 댓글 임베딩부; 상기 의미 벡터 간의 유사도를 산출하여 "
                    "유사 댓글 그룹을 생성하는 군집화부; 및 상기 유사 댓글 그룹별로 대표 댓글을 "
                    "생성하여 출력하는 대표 댓글 생성부를 포함하는 의미 기반 댓글 통합 시스템."
                ),
            },
            {
                "claim_no": 2,
                "is_dependent": True,
                "cited_claim_no": [1],
                "category": "시스템",
                "content": (
                    "제1항에 있어서, 상기 대표 댓글 생성부는 유사 댓글 그룹에 포함된 댓글들의 "
                    "공통 의미를 요약하여 하나의 대표 문장을 생성하는 의미 기반 댓글 통합 시스템."
                ),
            },
        ]
    }

    payload_path = sys.argv[1] if len(sys.argv) > 1 else None
    if payload_path and os.path.exists(payload_path):
        with open(payload_path, encoding="utf-8") as f:
            sample_claims = json.load(f)

    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    sample_state: PatentState = {
        "mock_input_data": {},
        "summary_data": None,
        "claims_data": ClaimResult.model_validate(sample_claims),
        "prior_art_data": None,
        "examiner_data": None,
    }

    result = run_prior_art_agent(sample_state, top_n=top_n)
    print("\n" + "=" * 60)
    print(result["prior_art_data"].model_dump_json(indent=2))
