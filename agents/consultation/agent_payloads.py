import uuid
import datetime

def build_invention_payload(state, user_id, consultation_idx):
    """
    상담 에이전트의 현재 상태(state)를 바탕으로 마스터 invention_payload를 생성합니다.
    (invention_extraction_guide.md 의 최종 JSON 구조를 따름)
    """
    payload_id = str(uuid.uuid4())
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # 1. Detail Elements 매핑 및 빈 값 필터링
    detail_elements = []
    type_map = {
        "implementations": "implementation",
        "parameters": "parameter",
        "algorithms": "algorithm",
        "optional_features": "optional",
        "error_handling": "error_handling"
    }
    
    for state_key, element_type in type_map.items():
        items = [str(x).strip() for x in state.get(state_key, []) if x and str(x).strip()]
        for i, item in enumerate(items):
            detail_elements.append({
                "element_type": element_type,
                "seq": i + 1,
                "content": item
            })
            
    # 2. Algorithm Steps 매핑
    algorithm_steps = []
    for i, step in enumerate(state.get("algorithm_steps", [])):
        step_str = str(step).strip()
        if step_str:
            algorithm_steps.append({
                "step_seq": i + 1,
                "step_content": step_str
            })

    # 3. DB Payload (DB 저장 전용 컬럼)
    db_payload = {
        "consulting": {
            "user_id": user_id,
            "consultation_idx": consultation_idx,
            "raw_chat_log": state.get("raw_log", []),
            "uploaded_file_path": state.get("file_path"),
            "summary_problem": state.get("problem"),
            "summary_solution": state.get("solution"),
            "summary_difference": state.get("differentiation"),
            "summary_effect": state.get("effect"),
        },
        "algorithm_steps": algorithm_steps,
        "detail_elements": detail_elements
    }
    
    # 4. Extended Info 및 Overall Flow Fallback 처리
    overall_flow_val = state.get("overall_flow")
    if not overall_flow_val and algorithm_steps:
        overall_flow_val = " ".join([f"{s['step_seq']}단계: {s['step_content']}" for s in algorithm_steps])
        
    extended_info = {
        "overall_flow": {
            "value": overall_flow_val
        }
    }
    
    # 5. Traceability (기본 출처 기록)
    traceability = {
        "db_payload.consulting.summary_problem": {
            "source": "state.problem",
            "source_type": "consultation_state"
        },
        "db_payload.consulting.summary_solution": {
            "source": "state.solution",
            "source_type": "consultation_state"
        },
        "db_payload.consulting.summary_difference": {
            "source": "state.differentiation",
            "source_type": "consultation_state"
        },
        "db_payload.consulting.summary_effect": {
            "source": "state.effect",
            "source_type": "consultation_state"
        }
    }
    
    # 6. Missing Information (최소 검증 로직 및 status 부여)
    missing_information = []
    if not state.get("problem"):
        missing_information.append({
            "field": "problem",
            "status": "missing",
            "reason": "기존 기술의 문제점이 비어 있습니다.",
            "question": "기존 기술이나 제품에서 어떤 불편함이 있었습니까?",
            "priority": "high"
        })
    if not state.get("solution"):
        missing_information.append({
            "field": "solution",
            "status": "missing",
            "reason": "해결 방법이 비어 있습니다.",
            "question": "그 문제를 어떤 방식으로 해결합니까?",
            "priority": "high"
        })
    if not state.get("differentiation"):
        missing_information.append({
            "field": "differentiation",
            "status": "missing",
            "reason": "기존 기술 대비 차별점이 비어 있습니다.",
            "question": "기존 기술과 비교했을 때 본 발명의 가장 큰 차별점은 무엇입니까?",
            "priority": "high"
        })
    if not state.get("effect"):
        missing_information.append({
            "field": "effect",
            "status": "missing",
            "reason": "기대효과가 비어 있습니다.",
            "question": "이 발명으로 어떤 효과가 발생합니까?",
            "priority": "high"
        })
    if len(algorithm_steps) < 3:
        missing_information.append({
            "field": "algorithm_steps",
            "status": "missing",
            "reason": f"알고리즘 단계가 부족합니다 (현재 {len(algorithm_steps)}단계).",
            "question": "발명이 실제로 작동하는 순서를 3단계 이상으로 설명해 주실 수 있습니까?",
            "priority": "high"
        })
        
    # 7. Validation Rules (TODO: 향후 실제 런타임 검증 로직 구현 예정)
    # 현재는 invention.json 스키마 기준을 명시하는 플레이스홀더(Placeholder) 역할입니다.
    validation_rules = {
        "db_payload_only_contains_current_db_columns": True,
        "extended_info_is_not_direct_db_payload": True,
        "every_core_summary_has_traceability": True,
        "missing_information_requires_field_reason_question_priority": True,
        "no_example_specific_field_inside_db_payload": True
    }
    
    return {
        "payload_id": payload_id,
        "created_at": now,
        "metadata": {
            "schema_version": "1.0",
            "source_type": "consultation_agent",
            "extracted_at": now,
        },
        "db_payload": db_payload,
        "extended_info": extended_info,
        "traceability": traceability,
        "missing_information": missing_information,
        "validation_rules": validation_rules
    }

def _create_envelope(agent_name, source_payload_id, input_data, traceability=None):
    """모든 후속 에이전트 payload에 들어가는 공통 Envelope(봉투) 메타데이터 구조"""
    return {
        "payload_id": str(uuid.uuid4()),
        "source_payload_id": source_payload_id,
        "agent": agent_name,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "input": input_data,
        "traceability": traceability or {}
    }


def build_prior_art_payload(invention_payload):
    """
    [선행기술 조사 에이전트용 Payload]
    """
    input_data = {
        "overall_flow": invention_payload.get("extended_info", {}).get("overall_flow", {}).get("value") or ""
    }
    
    return _create_envelope(
        "prior_art", 
        invention_payload["payload_id"], 
        input_data, 
        traceability=invention_payload.get("traceability", {})
    )


def build_claim_payload(invention_payload):
    """
    [청구항 에이전트용 Payload]
    """
    db_payload = invention_payload.get("db_payload", {})
    consulting = db_payload.get("consulting", {})
    
    input_data = {
        "overall_flow": invention_payload.get("extended_info", {}).get("overall_flow", {}).get("value") or "",
        "differentiation": consulting.get("summary_difference")
    }
    
    return _create_envelope(
        "claim", 
        invention_payload["payload_id"], 
        input_data, 
        traceability=invention_payload.get("traceability", {})
    )


def build_specification_payload(invention_payload):
    """
    [발명의 설명 에이전트용 Payload]
    """
    input_data = {
        "invention_data": invention_payload
    }
    
    return _create_envelope(
        "specification", 
        invention_payload["payload_id"], 
        input_data, 
        traceability=invention_payload.get("traceability", {})
    )
