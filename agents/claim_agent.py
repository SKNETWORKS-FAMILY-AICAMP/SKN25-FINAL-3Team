import json
import logging
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langsmith import traceable

from agents.core.state import PatentState, ParsedInvention, ClaimResult, ClaimItem

logger = logging.getLogger(__name__)

@traceable(name="Generate Claims Structure (Rule-Based)")
def generate_claims_structure(parsed_data: ParsedInvention) -> ClaimResult:
    """
    [Rule-Based] ParsedInvention 데이터를 바탕으로 청구항 뼈대를 생성합니다.
    최초 생성 시에만 사용됩니다.
    """
    components = parsed_data.get("architecture", {}).get("components", [])
    problem_text = parsed_data.get("technical_context", {}).get("problem_to_solve", "")
    effect_text = parsed_data.get("technical_context", {}).get("expected_effect", "")
    
    claims_list: List[ClaimItem] = []
    current_claim_no = 1
    
    if not components:
        return {"claims": []}

    # [STEP 1] 독립항 생성
    main_comp = components[0]
    category_str = parsed_data.get("invention_metadata", {}).get("category", "SYSTEM")
    
    # 🌟 수정 3: TypedDict 스키마 Literal["방법", "시스템", "CRM"]에 맞게 매핑 수정
    category_map = {
        "METHOD": "방법", 
        "SYSTEM": "시스템", 
        "PROGRAM": "CRM", 
        "APPARATUS": "시스템"
    }
    category = category_map.get(category_str, "시스템")

    content = (
        f"[해결과제: {problem_text}]를 해결하기 위한 {main_comp['name']}로서, "
        f"상기 {main_comp['name']}의 세부 메커니즘을 포함하여 [기대효과: {effect_text}]를 특징으로 하는 {category}."
    )
    
    claims_list.append({
        "claim_no": current_claim_no,
        "is_dependent": False,
        "cited_claim_no": [],
        "category": category, 
        "content": content
    })
    
    parent_claim_no = current_claim_no
    current_claim_no += 1

    # [STEP 2] 종속항 생성
    for sub_comp in components[1:]:
        content = (
            f"제{parent_claim_no}항에 있어서, "
            f"상기 {main_comp['name']}는, "
            f"{sub_comp['name']}을(를) 더 포함하는 것을 특징으로 하는 {category}."
        )
        
        claims_list.append({
            "claim_no": current_claim_no,
            "is_dependent": True,
            "cited_claim_no": [parent_claim_no],
            "category": category,
            "content": content
        })
        current_claim_no += 1

    return {"claims": claims_list}

class ClaimGenerationAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)

    def run(self, state: PatentState) -> Dict[str, Any]:
        logger.info("[Claim Agent] 청구항 생성/보정 노드 시작...")
        
        parsed_data = state.get("summary_data")
        if not parsed_data:
            logger.error("State에 summary_data가 존재하지 않습니다.")
            raise ValueError("State에 summary_data가 존재하지 않습니다.")
        
        # 🌟 수정 1: 심사관 피드백 및 이전 청구항 데이터 확인
        examiner_data = state.get("examiner_data")
        previous_claims_data = state.get("claims_data")
        
        is_rejection_loop = False
        rejection_reasons = ""

        # 거절 사유가 존재하는 경우 (루프를 타고 돌아온 경우)
        if examiner_data and not examiner_data.get("is_approved") and previous_claims_data:
            is_rejection_loop = True
            rejections = examiner_data.get("rejections", [])
            rejection_lines = [f"- 대상 청구항: {r.get('claims')} / 사유: {r.get('reason_text')}" for r in rejections]
            rejection_reasons = "\n".join(rejection_lines)

        system_prompt = (
            "당신은 대한민국의 베테랑 특허출원 전문 변리사입니다.\n"
            "제공된 청구항 JSON 구조의 'claim_no', 'is_dependent', 'cited_claim_no', 'category' 데이터는 "
            "특허법적 인용 관계를 고려하여 철저히 계산된 뼈대이므로 절대로 수정하거나 가공하지 마십시오.\n\n"
            "당신의 임무는 오직 각 청구항의 'content' 문자열을 대한민국 특허 실무 규정에 맞는 "
            "세련되고 유기적인 청구범위 문체(예: ~을 특징으로 하는 방법.)로 확장하고 다듬는 것입니다."
        )
        
        if is_rejection_loop:
            logger.info("[Claim Agent] 심사관 거절 사유를 반영하여 기존 청구항을 보정합니다.")
            user_prompt = (
                f"이전에 작성된 청구항에 대해 특허 심사관의 [거절 이유]가 통지되었습니다.\n"
                f"아래의 거절 이유를 꼼꼼히 분석하여, [이전 청구항]의 문제점을 완전히 해소한 새로운 청구항을 작성해 주세요.\n\n"
                # 🌟 [추가된 강력한 제약 조건]
                f"⚠️ [매우 중요] 'claim_no', 'is_dependent', 'cited_claim_no', 'category' 값은 [이전 청구항]의 값과 반드시 100% 동일하게 유지하고, 거절 이유를 해소하기 위해 오직 'content' 영역의 문장만 수정하십시오.\n\n"
                f"=== [거절 이유] ===\n{rejection_reasons}\n\n"
                f"=== [이전 청구항] ===\n{json.dumps(previous_claims_data, ensure_ascii=False)}\n\n"
            )
        else:
            logger.info("[Claim Agent] 요약 데이터를 바탕으로 최초 청구항을 생성합니다.")
            base_claim_structure = generate_claims_structure(parsed_data)
            user_prompt = (
                f"아래의 청구항 뼈대 구조를 바탕으로 content 영역의 문장을 변리사답게 다듬어 주세요.\n"
                f"입력 데이터: {json.dumps(base_claim_structure, ensure_ascii=False)}"
            )
        
        structured_llm = self.llm.with_structured_output(ClaimResult)
        
        refined_claims: ClaimResult = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        logger.info("[Claim Agent] 청구항 생성/보정 완료.")
        return {"claims_data": refined_claims}