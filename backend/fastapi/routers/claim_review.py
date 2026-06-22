"""사용자 작성 청구항의 심사·자동 보정 스트리밍 API."""

import asyncio
import json
import logging
import re
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.core.claim_review_graph import build_claim_review_graph
from agents.core.state import ClaimItem, ClaimResult


logger = logging.getLogger(__name__)
router = APIRouter()


class ClaimReviewRequest(BaseModel):
    claim_text: str = Field(min_length=10, max_length=200_000)


CLAIM_HEADER_PATTERN = re.compile(
    r"(?m)^\s*(?:【\s*)?청구항\s*(?:제\s*)?(\d+)\s*(?:항)?\s*(?:】|[.:])?\s*"
)


def infer_claim_category(content: str) -> Literal["방법", "시스템", "CRM"]:
    normalized = content.rstrip().rstrip(".。").rstrip()
    if re.search(r"(?:컴퓨터\s*판독\s*가능|기록\s*매체|기록매체)$", normalized):
        return "CRM"
    if re.search(r"(?:방법|단계)$", normalized):
        return "방법"
    return "시스템"


def parse_claim_text(claim_text: str) -> ClaimResult:
    """붙여넣은 청구범위에서 번호·인용관계·카테고리를 자동 추출한다."""
    text = claim_text.strip()
    matches = list(CLAIM_HEADER_PATTERN.finditer(text))

    if matches:
        claim_sections = [
            (
                int(match.group(1)),
                text[match.end(): matches[index + 1].start() if index + 1 < len(matches) else len(text)].strip(),
            )
            for index, match in enumerate(matches)
        ]
    else:
        claim_sections = [(1, text)]

    claim_sections = [(claim_no, content) for claim_no, content in claim_sections if content]
    if not claim_sections:
        raise ValueError("심사할 청구항 내용을 입력해 주세요.")
    if len(claim_sections) > 20:
        raise ValueError("한 번에 최대 20개 청구항까지 심사할 수 있습니다.")

    claims = []
    for claim_no, content in claim_sections:
        cited_claim_no = sorted({
            int(number)
            for number in re.findall(r"제\s*(\d+)\s*항", content)
            if int(number) != claim_no
        })
        claims.append(ClaimItem(
            claim_no=claim_no,
            is_dependent=bool(cited_claim_no),
            cited_claim_no=cited_claim_no,
            category=infer_claim_category(content),
            content=content,
        ))

    return ClaimResult(claims=claims)


def serialize_model(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return value.__dict__ if hasattr(value, "__dict__") else value


@router.post("/review-claims")
async def review_claims_worker(payload: ClaimReviewRequest):
    """최초 심사, 필요 시 보정, 재심사 결과를 NDJSON으로 순차 반환한다."""
    try:
        original_claims = parse_claim_text(payload.claim_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    initial_state = {
        "mock_input_data": {},
        "summary_data": None,
        "claims_data": original_claims,
        "prior_art_data": None,
        "examiner_data": None,
    }

    async def event_stream():
        final_state = dict(initial_state)
        examination_count = 0
        was_rewritten = False
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        yield json.dumps(
            {"step": "start", "message": "사용자 청구항을 심사관에게 전달했습니다."},
            ensure_ascii=False,
        ) + "\n"

        try:
            def run_graph():
                try:
                    compiled_graph = build_claim_review_graph()
                    for output in compiled_graph.stream(initial_state):
                        for node_name, state_update in output.items():
                            loop.call_soon_threadsafe(
                                queue.put_nowait,
                                ("update", node_name, state_update),
                            )
                except Exception as exc:  # 예외는 이벤트 루프로 전달한다.
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, ("done",))

            loop.run_in_executor(None, run_graph)

            while True:
                item = await queue.get()
                if item[0] == "done":
                    break
                if item[0] == "error":
                    raise item[1]

                _, node_name, state_update = item
                final_state.update(state_update)

                if node_name == "examiner_node":
                    examination_count += 1
                    examiner_data = state_update.get("examiner_data")
                    examiner_json = serialize_model(examiner_data)
                    is_approved = bool(examiner_json and examiner_json.get("is_approved"))
                    phase = "initial" if examination_count == 1 else "reexamination"
                    message = (
                        "명확성 심사를 통과했습니다."
                        if is_approved
                        else (
                            "보정 청구항이 재심사를 통과하지 못했습니다."
                            if phase == "reexamination"
                            else "명확성 보완이 필요해 자동 보정을 시작합니다."
                        )
                    )
                    yield json.dumps(
                        {
                            "step": "examination",
                            "phase": phase,
                            "message": message,
                            "examiner": examiner_json,
                        },
                        ensure_ascii=False,
                    ) + "\n"

                elif node_name == "rewrite_node":
                    was_rewritten = True
                    rewritten_claims = serialize_model(state_update.get("claims_data"))
                    yield json.dumps(
                        {
                            "step": "rewrite",
                            "message": "거절 사유를 반영한 보정안을 작성했습니다. 재심사를 진행합니다.",
                            "claims": rewritten_claims.get("claims", []) if rewritten_claims else [],
                        },
                        ensure_ascii=False,
                    ) + "\n"

            final_claims = serialize_model(final_state.get("claims_data"))
            final_examiner = serialize_model(final_state.get("examiner_data"))
            yield json.dumps(
                {
                    "step": "done",
                    "approved": bool(final_examiner and final_examiner.get("is_approved")),
                    "was_rewritten": was_rewritten,
                    "original_claims": original_claims.model_dump()["claims"],
                    "final_claims": final_claims.get("claims", []) if final_claims else [],
                    "examiner": final_examiner,
                },
                ensure_ascii=False,
            ) + "\n"

        except Exception as exc:
            logger.exception("청구항 심사 API 처리 실패")
            yield json.dumps(
                {"step": "error", "message": f"심사 처리 중 오류가 발생했습니다: {exc}"},
                ensure_ascii=False,
            ) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
