"""Unit tests for examiner parsing, revision counting, and fallbacks."""

import json

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from agents import examiner
from agents.core.state import ExaminerResult


def _agent_with_response(content):
    agent = examiner.ExaminerAgent.__new__(examiner.ExaminerAgent)
    agent.llm = RunnableLambda(lambda _prompt: AIMessage(content=content))
    return agent


def test_extract_payload_accepts_fenced_nested_json():
    payload = examiner.extract_payload(
        "prefix ```json\n"
        + json.dumps(
            {
                "examiner_result": {
                    "is_approved": False,
                    "rejections": [{"claims": [1], "reason_text": "불명확"}],
                }
            },
            ensure_ascii=False,
        )
        + "\n``` suffix"
    )

    assert payload["is_approved"] is False
    assert payload["rejections"][0]["claims"] == [1]


def test_extract_payload_salvages_malformed_json():
    payload = examiner.extract_payload('is_approved: false, "claims": [1, 3]')

    assert payload == {
        "is_approved": False,
        "rejections": [
            {
                "claims": [1, 3],
                "reason_text": "정규식 복구됨: 심사 모델이 거절 사유를 생성했으나 포맷 오류로 상세 텍스트를 불러오지 못했습니다.",
            }
        ],
    }


def test_format_claims_for_prompt_preserves_claim_order(claim_result):
    agent = examiner.ExaminerAgent.__new__(examiner.ExaminerAgent)

    text = agent.format_claims_for_prompt(claim_result)

    assert text.index("청구항 1") < text.index("청구항 2")
    assert claim_result.claims[0].content in text


def test_run_returns_none_when_claims_are_missing():
    agent = _agent_with_response("{}")

    assert agent.run({"claims_data": None}) == {"examiner_data": None}


def test_run_builds_examiner_result_and_increments_revision(claim_result):
    agent = _agent_with_response(
        json.dumps(
            {
                "is_approved": True,
                "rejections": [],
            }
        )
    )
    previous = ExaminerResult(is_approved=False, rejections=[], revision_count=1)

    result = agent.run({"claims_data": claim_result, "examiner_data": previous})

    assert result["examiner_data"].is_approved is True
    assert result["examiner_data"].revision_count == 2


def test_run_returns_safe_rejection_when_llm_fails(claim_result):
    def fail(_prompt):
        raise RuntimeError("LLM unavailable")

    agent = examiner.ExaminerAgent.__new__(examiner.ExaminerAgent)
    agent.llm = RunnableLambda(fail)

    result = agent.run({"claims_data": claim_result})

    assert result["examiner_data"] == ExaminerResult(
        is_approved=False,
        rejections=[],
        revision_count=1,
    )
