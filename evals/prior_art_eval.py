"""
선행기술조사 에이전트 통합 평가
- 실행: python -m evals.prior_art_eval

평가 지표:
  1. faithfulness     : 에이전트 분석이 선행특허 원문에 근거하는가 (RAGAS)
  2. answer_relevance : 분석이 청구항 구성요소를 구체적으로 다루는가 (GPT-4o)
"""

import sys
import os
import types
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# ragas가 삭제된 langchain_community 경로를 참조하는 문제 우회
if "langchain_community.chat_models.vertexai" not in sys.modules:
    from langchain_google_vertexai import ChatVertexAI
    _mod = types.ModuleType("langchain_community.chat_models.vertexai")
    _mod.ChatVertexAI = ChatVertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _mod

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from openai import OpenAI

from agents.core.state import PatentState, ClaimResult
from agents.prior_art_agent.prior_art_agent import run_prior_art_agent

oai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TEST_CLAIMS = [
    {
        "label": "AI-댓글통합",
        "question": (
            "복수의 사용자 댓글을 입력받는 입력부; 상기 복수의 사용자 댓글 각각을 "
            "의미 벡터로 변환하는 댓글 임베딩부; 상기 의미 벡터 간의 유사도를 산출하여 "
            "유사 댓글 그룹을 생성하는 군집화부; 및 상기 유사 댓글 그룹별로 대표 댓글을 "
            "생성하여 출력하는 대표 댓글 생성부를 포함하는 의미 기반 댓글 통합 시스템."
        ),
    },
    {
        "label": "AI-언어모델학습",
        "question": (
            "학습 데이터를 수신하는 단계; 트랜스포머 기반 언어 모델에 상기 학습 데이터를 "
            "입력하여 파라미터를 업데이트하는 미세조정 단계; 및 미세조정된 모델을 이용하여 "
            "자연어 질의에 대한 응답을 생성하는 단계를 포함하는 대화형 AI 모델 학습 방법."
        ),
    },
    {
        "label": "AI-이미지분류",
        "question": (
            "입력 이미지를 수신하는 수신부; 합성곱 신경망을 이용하여 상기 입력 이미지에서 "
            "특징 맵을 추출하는 특징 추출부; 및 상기 특징 맵을 복수의 카테고리로 분류하는 "
            "분류부를 포함하는 딥러닝 기반 이미지 분류 시스템."
        ),
    },
]


def build_ragas_answer(prior_art) -> str:
    if prior_art is None:
        return ""
    parts = []
    for c in prior_art.candidates:
        parts.extend(c.evidence)
    return " ".join(filter(None, parts))


def eval_answer_relevance(query: str, candidates: list) -> float:
    if not candidates:
        return 0.0

    top = candidates[0]
    overlap = " / ".join(top.overlap_points) if top.overlap_points else ""
    diff    = " / ".join(top.difference_points) if top.difference_points else ""

    prompt = f"""특허 청구항에 대한 선행기술 분석이 얼마나 청구항을 구체적으로 다루는지 평가하세요.
0.0~1.0 사이 실수 하나만 출력하세요.

평가 기준:
0.0~0.2: 분석이 청구항 구성요소를 전혀 언급하지 않음
0.3~0.5: 일부 구성요소만 다루거나 추상적으로만 언급
0.6~0.7: 주요 구성요소를 언급하나 근거가 부족함
0.8~0.9: 청구항 구성요소를 구체적 근거와 함께 분석
1.0    : 모든 구성요소를 청구항 용어를 직접 참조하며 정밀 분석

[청구항]
{query}

[청구항 구성요소별 분석 결과]
겹치는 구성요소: {overlap}
다른 구성요소: {diff}
리스크: {top.risk_level}

※ 평가 시 '겹치는 구성요소'와 '다른 구성요소'가 청구항의 구성요소를 얼마나 구체적으로 다루는지만 판단하세요."""

    resp = oai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=5,
        temperature=0,
    )
    try:
        score = float(resp.choices[0].message.content.strip())
        return max(0.0, min(1.0, score))
    except ValueError:
        return 0.0


def run():
    print("=" * 65)
    print("선행기술조사 에이전트 통합 평가 (faithfulness + answer_relevance)")
    print("=" * 65)

    questions, ragas_answers, contexts_list, ar_scores, labels = [], [], [], [], []

    for i, tc in enumerate(TEST_CLAIMS, 1):
        question = tc["question"]
        label    = tc["label"]
        print(f"\n▶ [{label}] {question[:50]}...")

        state: PatentState = {
            "mock_input_data": {},
            "summary_data": None,
            "claims_data": ClaimResult.model_validate({
                "claims": [{
                    "claim_no": 1, "is_dependent": False,
                    "cited_claim_no": [], "category": "시스템",
                    "content": question,
                }]
            }),
            "prior_art_data": None,
            "examiner_data": None,
        }

        agent_result = run_prior_art_agent(state, top_n=1)
        prior_art    = agent_result.get("prior_art_data")
        candidates   = prior_art.candidates if prior_art else []

        # contexts: 검색된 선행특허 원문
        ctx = [
            f"{p['title']}\n{p['abstract']}\n{p['claims']}"
            for p in agent_result.get("retrieved_patents", [])
        ]

        # answer_relevance 평가
        ar = eval_answer_relevance(question, candidates)
        print(f"  answer_relevance : {ar:.2f}")

        questions.append(question)
        ragas_answers.append(build_ragas_answer(prior_art))
        contexts_list.append(ctx)
        ar_scores.append(ar)
        labels.append(label)

    # faithfulness 평가 (RAGAS)
    print("\n[RAGAS faithfulness 평가 중...]")
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": ragas_answers,
        "contexts": contexts_list,
    })
    judge_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
    ragas_result = evaluate(dataset, metrics=[faithfulness], llm=judge_llm)
    df = ragas_result.to_pandas()

    # 최종 요약
    print("\n" + "=" * 70)
    print(f"{'케이스':<20} {'faithfulness':^14} {'answer_relevance':^16} {'종합':^8}")
    print("-" * 70)
    total_f, total_ar = 0.0, 0.0
    for label, f_score, ar_score in zip(labels, df["faithfulness"], ar_scores):
        f_score = f_score if f_score is not None else 0.0
        avg = (f_score + ar_score) / 2
        total_f += f_score
        total_ar += ar_score
        print(f"{label:<20} {f_score:^14.2f} {ar_score:^16.2f} {avg:^8.2f}")
    n = len(ar_scores)
    print("-" * 70)
    avg_f  = total_f / n
    avg_ar = total_ar / n
    print(f"{'평균':<20} {avg_f:^14.2f} {avg_ar:^16.2f} {(avg_f + avg_ar) / 2:^8.2f}")
    print("=" * 70)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없습니다.")
        sys.exit(1)
    run()
