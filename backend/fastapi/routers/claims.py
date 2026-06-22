# backend/fastapi/routers/claims.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
import logging

from agents.core.graph import build_patent_graph
from agents.prior_art_agent.prior_art_agent import run_prior_art_agent

from fastapi.concurrency import run_in_threadpool
import asyncio

import uuid
from backend.fastapi.judge.claim_evaluator import background_llm_judge

logger = logging.getLogger(__name__)
router = APIRouter()  # 💡 app = FastAPI() 대신 APIRouter()를 사용합니다!

def safe_serialize(obj):
    if hasattr(obj, 'model_dump'): return obj.model_dump()
    elif hasattr(obj, '__dict__'): return obj.__dict__
    return str(obj)



@router.post("/generate-claims")
async def generate_claims_worker(request: Request):
    """장고가 보낸 데이터를 받아 랭그래프를 돌리고 스트리밍으로 반환"""
    data = await request.json()
    initial_state = data.get("initial_state")

    # 1. ⭐️ 이번 실행(Trace)의 고유 ID를 직접 생성합니다.
    import uuid
    current_run_id = uuid.uuid4()

    # 이 config를 graph.stream에 넘겨주면 LangSmith가 이 ID로 로그를 기록합니다.
    config = {
        "run_id": current_run_id,
        "run_name": "Patent_Claims_Generation" 
    }

    def is_valid(val):
        return bool(val and val.strip() != "미파악")

    async def event_stream():        
        try:
            yield json.dumps({"step": "start", "message": "FastAPI AI 워커 가동 시작"}) + "\n"
            
            compiled_graph = build_patent_graph()
            final_state = {}
            queue = asyncio.Queue()


            def run_graph():
                for output in compiled_graph.stream(initial_state, config=config):
                    for node_name, state_update in output.items():
                        queue.put_nowait((node_name, state_update))
                queue.put_nowait(None) 

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, run_graph)

            while True:
                item = await queue.get()
                if item is None:
                    break

                node_name, state_update = item
                final_state.update(state_update)

                safe_state = {k: safe_serialize(v) for k, v in state_update.items()}
                yield json.dumps({
                    "step": "log_and_state",
                    "log_msg": f"[{node_name.upper()}] 에이전트 처리 완료",
                    "state_data": safe_state
                }) + "\n"


                if node_name == "summary_node":
                    yield json.dumps({"step": "summary", "message": "발명 내용 구조화 완료!"}) + "\n"
                elif node_name == "claim_node":
                    yield json.dumps({"step": "claim", "message": "청구항 초안 작성 완료!"}) + "\n"
                elif node_name == "examiner_node":
                    examiner_data = state_update.get("examiner_data")
                    if examiner_data and not getattr(examiner_data, 'is_approved', True):
                        yield json.dumps({"step": "rewrite", "message": "심사관 반려! 보정 진행"}) + "\n"
                    else:
                        yield json.dumps({"step": "examiner", "message": "심사관 승인 완료!"}) + "\n"
                elif node_name == "rewrite_node":
                    yield json.dumps({"step": "rewrite_done", "message": "보정 완료! 재심사 요청 중..."}) + "\n"

                    

            claims_result = final_state.get("claims_data")
            examiner_result = final_state.get("examiner_data")

            loop_count = examiner_result.revision_count if examiner_result else 0
            claim_result_text = f"📜 **[AI 멀티에이전트 최종 청구범위 발행 완료]**\n(AI 심사관 검수 통과: {loop_count}회 루프)\n\n"
            
            # 2. 선행기술조사 실행 (에이전트가 처리하도록)
            yield json.dumps({"step": "prior_art_start", "message": "선행기술조사 에이전트 가동 (기술 분야 분석 중)..."}) + "\n"
            
            pa_data = None
            try:
                prior_art_result = await run_in_threadpool(run_prior_art_agent, final_state, 3)
                if "prior_art_data" in prior_art_result:
                    pa_data = prior_art_result["prior_art_data"].model_dump()
                    yield json.dumps({
                        "step": "prior_art_done", 
                        "prior_art_data": pa_data
                    }) + "\n"
            except Exception as e:
                logger.error(f"선기조 에러: {e}")

            # 3. 완료 신호 및 최종 데이터 장고로 전송
            claims_list = []
            if claims_result and getattr(claims_result, 'claims', None):
                for c in claims_result.claims:
                    type_badge = '[종속항]' if c.is_dependent else '[독립항]'
                    claim_result_text += f"**청구항 {c.claim_no} {type_badge}**\n{c.content}\n\n"
                    
                    claims_list.append({
                        "claim_no": c.claim_no,
                        "is_dependent": c.is_dependent,
                        "cited_claim_no": getattr(c, 'cited_claim_no', []),
                        "category": getattr(c, 'category', ''),
                        "content": c.content
                    })

            # ⭐️ 사용자에게 응답을 완료하기 직전, 백그라운드 태스크로 Judge를 실행합니다.
            # await를 쓰지 않고 태스크만 생성해 두면, 사용자는 기다리지 않고 즉시 응답을 받습니다.
            asyncio.create_task(background_llm_judge(
                run_id=current_run_id, 
                input_data=initial_state["mock_input_data"],
                generated_claims=claims_list
            ))

            yield json.dumps({
                "step": "done",
                "message_content": claim_result_text,
                "claims": claims_list,
                "prior_art_data": pa_data
            }) + "\n"

        except Exception as e:
            logger.error(f"FastAPI 에러: {e}")
            yield json.dumps({"step": "error", "message": str(e)}) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
