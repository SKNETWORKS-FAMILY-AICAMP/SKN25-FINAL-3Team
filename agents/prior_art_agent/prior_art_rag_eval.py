"""
선행기술조사 에이전트 RAG 품질 평가
- 실행: python agents/prior_art_agent/prior_art_rag_eval.py

평가 지표 3가지:
  1. retrieval_relevance  : 검색된 특허가 쿼리와 관련 있는가
  2. faithfulness         : evidence_sentences가 원문에 근거하는가 (할루시네이션 감지)
  3. answer_relevance     : 리스크 분석이 청구항에 실제로 답하는가
"""

import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from openai import OpenAI
from agents.core.state import PatentState, ClaimResult
from agents.prior_art_agent.prior_art_agent import search_similar_patents, run_prior_art_agent

oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────────────────────
# 테스트 청구항 (AI 도메인 → LOCAL_DB 경로만 사용)
# ─────────────────────────────────────────────────────────────
TEST_CLAIMS = [
    {
        "label": "AI-댓글통합",
        "content": (
            "복수의 사용자 댓글을 입력받는 입력부; 상기 복수의 사용자 댓글 각각을 "
            "의미 벡터로 변환하는 댓글 임베딩부; 상기 의미 벡터 간의 유사도를 산출하여 "
            "유사 댓글 그룹을 생성하는 군집화부; 및 상기 유사 댓글 그룹별로 대표 댓글을 "
            "생성하여 출력하는 대표 댓글 생성부를 포함하는 의미 기반 댓글 통합 시스템."
        ),
    },
    {
        "label": "AI-언어모델학습",
        "content": (
            "학습 데이터를 수신하는 단계; 트랜스포머 기반 언어 모델에 상기 학습 데이터를 "
            "입력하여 파라미터를 업데이트하는 미세조정 단계; 및 미세조정된 모델을 이용하여 "
            "자연어 질의에 대한 응답을 생성하는 단계를 포함하는 대화형 AI 모델 학습 방법."
        ),
    },
    {
        "label": "AI-이미지분류",
        "content": (
            "입력 이미지를 수신하는 수신부; 합성곱 신경망을 이용하여 상기 입력 이미지에서 "
            "특징 맵을 추출하는 특징 추출부; 및 상기 특징 맵을 복수의 카테고리로 분류하는 "
            "분류부를 포함하는 딥러닝 기반 이미지 분류 시스템."
        ),
    },
]

TOP_N = 3  # 검색할 특허 수


# ─────────────────────────────────────────────────────────────
# 평가 함수 1: Retrieval Relevance
# 검색된 특허가 쿼리 청구항과 관련 있는지 LLM이 판단
# ─────────────────────────────────────────────────────────────
def eval_retrieval_relevance(query: str, patents: list[dict]) -> dict:
    results = []
    for p in patents:
        title   = p.get("title", "")
        abstract = p.get("abstract", "")[:400]
        score   = p.get("similarity_score", 0.0)

        prompt = f"""특허 청구항과 검색된 선행특허가 기술적으로 관련 있는지 판단하세요.

[청구항]
{query}

[검색된 선행특허]
제목: {title}
요약: {abstract}

관련 있으면 1, 없으면 0을 숫자 하나만 출력하세요."""

        resp = oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=5,
            temperature=0,
        )
        llm_score = 1 if resp.choices[0].message.content.strip().startswith("1") else 0
        results.append({
            "title": title[:40],
            "similarity_score": score,
            "llm_relevant": llm_score,
        })

    relevant_count = sum(r["llm_relevant"] for r in results)
    precision = relevant_count / len(results) if results else 0.0
    avg_sim   = sum(r["similarity_score"] for r in results) / len(results) if results else 0.0
    return {
        "metric": "retrieval_relevance",
        "precision_at_k": round(precision, 2),  # 관련 있는 비율
        "avg_similarity_score": round(avg_sim, 4),
        "pass": precision >= 0.5,  # 기준: 절반 이상 관련
        "detail": results,
    }


# ─────────────────────────────────────────────────────────────
# 평가 함수 2: Faithfulness (할루시네이션 감지)
# evidence_sentences[].patent_text 가 실제 원문에 근거하는지 확인
# ─────────────────────────────────────────────────────────────
def eval_faithfulness(candidates: list, patents: list[dict]) -> dict:
    # patent_id → 원문 매핑
    source_map = {p["patent_id"]: p for p in patents}

    all_checks = [] 
    for cand in candidates:
        patent_id = cand.patent_id
        source    = source_map.get(patent_id, {})
        source_text = " ".join(filter(None, [
            source.get("claims", ""),
            source.get("abstract", ""),
        ]))[:2000]

        if not source_text or not cand.evidence:
            continue

        for ev_text in cand.evidence:
            if not ev_text:
                continue

            prompt = f"""아래 [원문]에 [근거문장]이 실제로 담겨 있거나 이를 올바르게 요약한 내용인지 판단하세요.
원문에 없는 내용을 지어낸 것이면 0, 근거가 있으면 1을 숫자 하나만 출력하세요.

[원문]
{source_text}

[근거문장]
{ev_text}"""

            resp = oai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=5,
                temperature=0,
            )
            grounded = 1 if resp.choices[0].message.content.strip().startswith("1") else 0
            all_checks.append({
                "patent_title": cand.title[:30],
                "evidence": ev_text[:60],
                "grounded": grounded,
            })

    if not all_checks:
        return {"metric": "faithfulness", "score": None, "pass": False, "detail": [], "note": "evidence 없음"}

    grounded_count = sum(c["grounded"] for c in all_checks)
    score = grounded_count / len(all_checks)
    return {
        "metric": "faithfulness",
        "score": round(score, 2),         
        "pass": score >= 0.7,              
        "detail": all_checks,
    }


# ─────────────────────────────────────────────────────────────
# 평가 함수 3: Answer Relevance
# 생성된 리스크 분석이 실제로 청구항에 답하는가
# ─────────────────────────────────────────────────────────────
def eval_answer_relevance(query: str, candidates: list) -> dict:
    if not candidates:
        return {"metric": "answer_relevance", "score": 0, "pass": False}

    top = candidates[0]
    overlap = " / ".join(top.overlap_points[:2]) if top.overlap_points else ""
    diff    = " / ".join(top.difference_points[:2]) if top.difference_points else ""

    prompt = f"""아래 [청구항]에 대한 [분석 결과]가 청구항의 내용을 실제로 다루고 있는지 판단하세요.
청구항과 무관한 일반적인 내용만 있으면 0, 청구항 구성요소를 구체적으로 언급하면 1을 숫자 하나만 출력하세요.

[청구항]
{query}

[분석 결과]
겹치는 점: {overlap}
다른 점: {diff}
리스크: {top.risk_level}"""

    resp = oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=5,
        temperature=0,
    )
    score = 1 if resp.choices[0].message.content.strip().startswith("1") else 0
    return {
        "metric": "answer_relevance",
        "score": score,
        "pass": score == 1,
        "top_candidate": top.title[:40],
        "risk_level": top.risk_level,
    }


# ─────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────
def run():
    print("=" * 65)
    print("선행기술조사 에이전트 RAG 품질 평가")
    print("=" * 65)

    summary_rows = []

    for tc in TEST_CLAIMS:
        label   = tc["label"]
        content = tc["content"]
        print(f"\n▶ [{label}] 테스트 시작")

        # 2) 전체 에이전트 실행 (generation 포함)
        state: PatentState = {
            "mock_input_data": {},
            "summary_data": None,
            "claims_data": ClaimResult.model_validate({
                "claims": [{
                    "claim_no": 1, "is_dependent": False,
                    "cited_claim_no": [], "category": "시스템",
                    "content": content,
                }]
            }),
            "prior_art_data": None,
            "examiner_data": None,
        }
        result     = run_prior_art_agent(state, top_n=TOP_N)
        patents = result.get("retrieved_patents", [])
        prior_art  = result.get("prior_art_data")
        candidates = prior_art.candidates if prior_art else []

        # 3) 평가
        r1 = eval_retrieval_relevance(content, patents)
        r2 = eval_faithfulness(candidates, patents)
        r3 = eval_answer_relevance(content, candidates)

        # 출력
        def mark(ok): return "PASS" if ok else "FAIL"
        print(f"  retrieval_relevance  : {mark(r1['pass'])}  "
              f"(precision={r1['precision_at_k']:.0%}, avg_sim={r1['avg_similarity_score']:.3f})")

        if r2.get("score") is not None:
            print(f"  faithfulness         : {mark(r2['pass'])}  "
                  f"(grounded={r2['score']:.0%} of {len(r2['detail'])} evidence)")
        else:
            print(f"  faithfulness         : SKIP  ({r2.get('note')})")

        print(f"  answer_relevance     : {mark(r3['pass'])}  "
              f"(risk={r3.get('risk_level','?')}, top={r3.get('top_candidate','?')})")

        summary_rows.append({
            "label": label,
            "retrieval": mark(r1["pass"]),
            "faithfulness": mark(r2["pass"]) if r2.get("score") is not None else "SKIP",
            "answer": mark(r3["pass"]),
        })

    # 최종 요약 테이블
    print("\n" + "=" * 65)
    print(f"{'케이스':<20} {'검색품질':^12} {'Faithfulness':^14} {'분석품질':^10}")
    print("-" * 65)
    for row in summary_rows:
        print(f"{row['label']:<20} {row['retrieval']:^12} {row['faithfulness']:^14} {row['answer']:^10}")
    print("=" * 65)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY가 없습니다.")
        sys.exit(1)
    run()
