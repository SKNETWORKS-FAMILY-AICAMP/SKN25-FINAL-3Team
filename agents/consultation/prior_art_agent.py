"""
선행기술조사 에이전트
- Supabase DB의 patent_corpus 테이블에서 특허 데이터 및 임베딩 로드
- invention_payload JSON → 쿼리 추출 → 임베딩 유사도 검색 → 근거문장 + 리스크 분석
"""

import os
import json
import re
from pathlib import Path
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

_ENV_DIR = Path(__file__).resolve().parent
load_dotenv(_ENV_DIR.parents[1] / ".env")
load_dotenv(_ENV_DIR / ".env", override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PATENTS_DIR = Path(os.getenv("PATENTS_TEXT_DIR", _ENV_DIR.parents[1] / "data" / "raw" / "texts" / "patents_txt"))  # load_corpus.py에서 사용

EMBED_MODEL   = "text-embedding-3-small"
EXTRACT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANALYZE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


# ─────────────────────────────────────────────────────────────
# 1. TXT 파일 로드 및 파싱
# ─────────────────────────────────────────────────────────────

def _parse_patent_txt(file_path: str) -> dict:
    """
    TXT 파일에서 특허 메타데이터와 본문을 파싱합니다.
    아래 두 가지 형식을 모두 지원합니다:

    [형식 A - 구조화]
    출원번호: 10-2025-0063559
    발명의 명칭: ...
    출원인: ...
    요약: ...
    청구항: ...
    발명의 설명: ...

    [형식 B - 비구조화]
    특별한 헤더 없이 특허 전문이 그대로 들어있는 경우 → 전체를 raw_text로 처리
    """
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    # 파일명에서 번호 추출 시도 (예: KR-10-2961552.txt, 1020250063559.txt)
    stem = Path(file_path).stem
    num_match = re.search(r"(\d{10,13})", stem)
    file_number = num_match.group(1) if num_match else stem

    meta = {
        "file_path": file_path,
        "file_name": Path(file_path).name,
        "patent_number": file_number,
        "title": "",
        "applicant": "",
        "abstract": "",
        "claims": "",
        "description": "",
        "raw_text": raw,
    }

    # 구조화 헤더 패턴 정의
    patterns = {
        "patent_number": r"(?:출원번호|등록번호|공개번호)\s*[:：]\s*(.+)",
        "title":         r"(?:발명의\s*명칭|제목|Title)\s*[:：]\s*(.+)",
        "applicant":     r"(?:출원인|특허권자|Applicant)\s*[:：]\s*(.+)",
        "abstract":      r"(?:요약|Abstract)\s*[:：]\s*([\s\S]+?)(?=\n(?:청구항|발명의\s*설명|[A-Z가-힣]{2,}\s*[:：])|$)",
        "claims":        r"(?:청구항|Claims?)\s*[:：]\s*([\s\S]+?)(?=\n(?:발명의\s*설명|상세한\s*설명|[A-Z가-힣]{2,}\s*[:：])|$)",
        "description":   r"(?:발명의\s*설명|상세한\s*설명|Description)\s*[:：]\s*([\s\S]+?)(?=\n(?:[A-Z가-힣]{2,}\s*[:：])|$)",
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, raw, re.IGNORECASE)
        if m:
            meta[key] = m.group(1).strip()[:3000]  # 필드별 최대 3000자

    # title이 없으면 첫 번째 비어있지 않은 줄을 제목으로 사용
    if not meta["title"]:
        for line in raw.splitlines():
            line = line.strip()
            if line and len(line) > 4:
                meta["title"] = line[:200]
                break

    return meta


def load_patent_corpus(patents_dir: str = None) -> list[dict]:
    """patents_txt/ 의 모든 .txt 파일을 로드하여 특허 목록 반환"""
    d = Path(patents_dir) if patents_dir else PATENTS_DIR
    if not d.exists():
        d.mkdir(parents=True)
        print(f"[선행기술조사] {d} 디렉토리를 생성했습니다. TXT 특허 파일을 넣어주세요.")
        return []

    files = list(d.glob("*.txt")) + list(d.glob("**/*.txt"))
    files = list(set(files))
    if not files:
        print(f"[선행기술조사] {d} 에 .txt 파일이 없습니다.")
        return []

    corpus = []
    for fp in files:
        try:
            patent = _parse_patent_txt(str(fp))
            corpus.append(patent)
        except Exception as e:
            print(f"[선행기술조사] {fp.name} 파싱 실패: {e}")

    print(f"[선행기술조사] 특허 코퍼스 {len(corpus)}건 로드 완료")
    return corpus


# ─────────────────────────────────────────────────────────────
# 2. 임베딩 유틸 (load_corpus.py에서도 재사용)
# ─────────────────────────────────────────────────────────────

def _embed_texts(texts: list[str]) -> np.ndarray:
    """OpenAI 임베딩 API 호출 (배치, 최대 100건씩)"""
    batch_size = 100
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vecs = [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
        all_vecs.extend(vecs)
    return np.array(all_vecs, dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 3. DB에서 코퍼스 + 임베딩 로드
# ─────────────────────────────────────────────────────────────

def load_corpus_from_db() -> tuple[np.ndarray, list[dict]]:
    """Supabase DB에서 특허 코퍼스와 임베딩을 로드합니다."""
    from patent_db import PatentCorpus, SessionLocal

    db = SessionLocal()
    try:
        patents = db.query(PatentCorpus).all()
        if not patents:
            print("[선행기술조사] DB에 특허 데이터가 없습니다. load_corpus.py를 먼저 실행하세요.")
            return np.array([]), []

        corpus, vectors = [], []
        for p in patents:
            corpus.append({
                "file_name":     p.file_name or "",
                "patent_number": p.patent_number or "",
                "title":         p.title or "",
                "applicant":     p.applicant or "",
                "abstract":      p.abstract or "",
                "claims":        p.claims or "",
                "description":   p.description or "",
                "raw_text":      p.raw_text or "",
            })
            vectors.append(p.embedding)

        print(f"[선행기술조사] DB에서 특허 {len(corpus)}건 로드 완료")
        return np.array(vectors, dtype=np.float32), corpus
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# 3. Payload → 검색 쿼리 텍스트 추출
# ─────────────────────────────────────────────────────────────

def _build_query_text(invention_payload: dict) -> str:
    """invention_payload에서 검색에 사용할 핵심 텍스트를 추출합니다."""
    consulting = invention_payload.get("db_payload", {}).get("consulting", {})
    steps = invention_payload.get("db_payload", {}).get("algorithm_steps", [])
    overall_flow = (
        invention_payload.get("extended_info", {})
        .get("overall_flow", {})
        .get("value", "")
    )

    parts = []
    if consulting.get("summary_problem"):
        parts.append(f"문제: {consulting['summary_problem']}")
    if consulting.get("summary_solution"):
        parts.append(f"해결책: {consulting['summary_solution']}")
    if consulting.get("summary_difference"):
        parts.append(f"차별점: {consulting['summary_difference']}")
    if overall_flow:
        parts.append(f"전체흐름: {overall_flow}")
    elif steps:
        step_text = " ".join(f"{s['step_seq']}단계: {s['step_content']}" for s in steps[:5])
        parts.append(f"알고리즘: {step_text}")

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────
# 4. 코사인 유사도 기반 Top-N 검색
# ─────────────────────────────────────────────────────────────

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norm @ a_norm


def search_similar_patents(
    query_text: str,
    vectors: np.ndarray,
    corpus: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """쿼리 텍스트와 코퍼스를 임베딩 비교하여 Top-N 특허를 반환합니다."""
    query_vec = _embed_texts([query_text])[0]
    scores = _cosine_similarity(query_vec, vectors)

    top_idx = np.argsort(scores)[::-1][:top_n]
    results = []
    for idx in top_idx:
        patent = dict(corpus[idx])
        patent["similarity_score"] = round(float(scores[idx]), 4)
        # raw_text는 LLM 분석에서 사용하므로 2000자로 제한
        patent["_search_text"] = patent["raw_text"][:2000]
        del patent["raw_text"]  # 응답 크기 절약
        results.append(patent)
    return results


# ─────────────────────────────────────────────────────────────
# 5. LLM 기반 근거 문장 + 리스크 분석
# ─────────────────────────────────────────────────────────────

def _analyze_patent(invention_payload: dict, patent: dict) -> dict:
    """GPT-4o를 사용해 선행특허 1건에 대한 근거 문장과 리스크를 추출합니다."""
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
        f"설명: {patent.get('description', '') or patent.get('_search_text', '')}",
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
  "evidence_sentences": [
    {{
      "patent_text": "선행특허의 해당 구절 (원문 그대로)",
      "invention_text": "발명의 대응 내용",
      "overlap_type": "동일|유사|관련"
    }}
  ],
  "risk_level": "high|medium|low",
  "risk_reasons": ["리스크 이유1", "리스크 이유2"],
  "differentiating_points": ["본 발명만의 차별점1", "차별점2"],
  "recommendation": "대응 전략 또는 보정 방향 (1~2문장)"
}}"""

    resp = client.chat.completions.create(
        model=ANALYZE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_completion_tokens=1500,
    )
    return json.loads(resp.choices[0].message.content)


# ─────────────────────────────────────────────────────────────
# 6. 전체 리스크 요약
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


# ─────────────────────────────────────────────────────────────
# 7. 메인 에이전트 함수
# ─────────────────────────────────────────────────────────────

def run_prior_art_agent(
    invention_payload: dict,
    top_n: int = 5,
) -> dict:
    """
    선행기술조사 에이전트 메인 함수.

    Args:
        invention_payload: build_invention_payload() 가 반환한 JSON
        top_n: 반환할 유사 선행특허 수

    Returns:
        {
            "prior_art_results": [...],   # Top-N 특허별 분석
            "overall_risk": {...},         # 전체 리스크 요약
            "query_text": "...",           # 사용된 검색 쿼리 텍스트
            "corpus_size": N,              # 검색 대상 특허 수
        }
    """
    # 1. DB에서 코퍼스 + 임베딩 로드
    vectors, corpus = load_corpus_from_db()
    if not corpus:
        return {
            "error": "DB에 특허 데이터가 없습니다. load_corpus.py를 먼저 실행하세요.",
            "prior_art_results": [],
            "overall_risk": {"level": "unknown", "summary": "코퍼스 없음"},
        }

    # 3. 검색 쿼리 텍스트 구성
    query_text = _build_query_text(invention_payload)
    print(f"[선행기술조사] 검색 쿼리:\n  {query_text[:200]}...")

    # 4. 유사도 검색
    top_patents = search_similar_patents(query_text, vectors, corpus, top_n=top_n)
    print(f"[선행기술조사] 유사 특허 Top-{top_n} 선정 완료")

    # 5. 근거 문장 + 리스크 분석 (특허별 LLM 호출)
    prior_art_results = []
    for i, patent in enumerate(top_patents):
        print(f"[선행기술조사] 분석 중 {i+1}/{len(top_patents)}: {patent.get('title', patent['file_name'])[:50]}")
        try:
            analysis = _analyze_patent(invention_payload, patent)
        except Exception as e:
            analysis = {
                "evidence_sentences": [],
                "risk_level": "unknown",
                "risk_reasons": [f"분석 실패: {str(e)}"],
                "differentiating_points": [],
                "recommendation": "",
            }

        prior_art_results.append({
            "rank": i + 1,
            "patent_number": patent.get("patent_number", ""),
            "title": patent.get("title", ""),
            "applicant": patent.get("applicant", ""),
            "file_name": patent["file_name"],
            "similarity_score": patent["similarity_score"],
            **analysis,
        })

    # 6. 전체 리스크 요약
    overall_risk = _summarize_overall_risk(prior_art_results)

    print(f"\n[선행기술조사] 완료 — 전체 리스크: {overall_risk['level'].upper()}")
    print(f"  {overall_risk['summary']}")

    return {
        "prior_art_results": prior_art_results,
        "overall_risk": overall_risk,
        "query_text": query_text,
        "corpus_size": len(corpus),
    }


# ─────────────────────────────────────────────────────────────
# CLI 실행 (테스트용)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # 테스트용 최소 페이로드
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
    print("\n" + "="*60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
