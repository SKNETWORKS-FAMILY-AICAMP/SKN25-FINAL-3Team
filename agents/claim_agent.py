import json
import logging
from typing import Dict, List, Any

from langchain_openai import ChatOpenAI
from agents.core.state import PatentState, ConsultationData, ClaimResult, ClaimItem, Element

logger = logging.getLogger(__name__)

def parent_map_desc(element_map: Dict[int, Element], parent_id: int) -> str:
    """부모 구성요소의 명칭을 정제해서 가져오는 헬퍼 함수"""
    full_desc = element_map[parent_id]['description']

    # 프롬프트나 로직에서 명칭만 자르기 위한 임시 파싱 (실무에서는 더 정교한 명사 추출 필요)
    return full_desc.split("하는")[-1].strip() if "하는" in full_desc else full_desc[:15]

def generate_claims_structure(consultation: ConsultationData) -> ClaimResult:
    """
    [Rule-Based] 요약 데이터를 바탕으로 특허법적 계층 구조를 가진 청구항 뼈대를 생성합니다.
    """
    elements = consultation["elements"]
    problems = consultation.get("problems", [])
    effects = consultation.get("effects", [])

    element_map: Dict[int, Element] = {el["element_id"]: el for el in elements}
    el_to_claim_map: Dict[int, int] = {}
    
    claims_list: List[ClaimItem] = []
    current_claim_no = 1

    # [STEP 1] 독립항 생성 (parent_id가 없는 최상위 요소)
    top_elements = [el for el in elements if el.get("parent_id") is None]
    
    for el in top_elements:
        el_id = el["element_id"]
        el_to_claim_map[el_id] = current_claim_no
        
        category = "시스템" if "시스템" in el["description"] else "방법"
        problem_text = problems[0] if problems else ""
        effect_text = effects[0] if effects else ""
        
        content = (
            f"[해결과제: {problem_text}]를 해결하기 위한 {el['description']}로서, "
            f"상기 {el['description']}의 세부 메커니즘을 포함하여 [기대효과: {effect_text}]를 특징으로 하는 {category}."
        )
        
        claims_list.append({
            "claim_no": current_claim_no,
            "is_dependent": False,
            "cited_claim_no": [],
            "category": category,
            "content": content
        })
        current_claim_no += 1

    # [STEP 2] 종속항 생성 (parent_id가 존재하는 세부 요소)
    sub_elements = [el for el in elements if el.get("parent_id") is not None]
    
    for el in sub_elements:
        el_id = el["element_id"]
        parent_id = el["parent_id"]
        parent_claim_no = el_to_claim_map.get(parent_id)
        
        if parent_claim_no is not None:
            el_to_claim_map[el_id] = current_claim_no
            parent_claim = next((c for c in claims_list if c["claim_no"] == parent_claim_no), None)
            category = parent_claim["category"]
            
            content = (
                f"제{parent_claim_no}항에 있어서, "
                f"상기 {parent_map_desc(element_map, parent_id)}는, "
                f"{el['description']}을(를) 더 포함하는 것을 특징으로 하는 {category}."
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
        # 모델명을 외부에서 주입받을 수 있도록 수정 (유연성 확보)
        # 청구항 구조를 건드리지 않고 문장만 다듬는 것이라 gpt-4o 또는 gpt-4o-mini 모두 적합합니다.
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)

    def run(self, state: PatentState) -> Dict[str, Any]:
        """
        LangGraph 노드 함수: 요약 데이터를 읽어 청구항을 생성(윤문)하고 반환합니다.
        """
        logger.info("[Claim Agent] 구조화된 출력을 활용한 청구항 생성 시작...")
        
        consultation_data = state.get("summary_data")
        if not consultation_data:
            logger.error("State에 summary_data가 존재하지 않습니다.")
            raise ValueError("State에 summary_data가 존재하지 않습니다. 요약 노드를 먼저 확인하세요.")
        
        # 1. 뼈대 생성 (Rule-based)
        base_claim_structure = generate_claims_structure(consultation_data)
        
        # 2. 프롬프트 작성
        system_prompt = (
            "당신은 대한민국의 베테랑 특허출원 전문 변리사입니다.\n"
            "제공된 청구항 JSON 구조의 'claim_no', 'is_dependent', 'cited_claim_no', 'category' 데이터는 "
            "특허법적 인용 관계를 고려하여 철저히 계산된 뼈대이므로 절대로 수정하거나 가공하지 마십시오.\n\n"
            "당신의 임무는 오직 각 청구항의 'content' 문자열을 대한민국 특허 실무 규정에 맞는 "
            "세련되고 유기적인 청구범위 문체(예: ~을 특징으로 하는 방법.)로 확장하고 다듬는 것입니다."
        )
        
        user_prompt = (
            f"아래의 청구항 뼈대 구조를 바탕으로 content 영역의 문장을 변리사답게 다듬어 주세요.\n"
            f"입력 데이터: {json.dumps(base_claim_structure, ensure_ascii=False)}"
        )
        
        # 3. LLM 호출 및 Pydantic(TypedDict) 포맷 강제
        structured_llm = self.llm.with_structured_output(ClaimResult)
        
        refined_claims: ClaimResult = structured_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        logger.info("[Claim Agent] 청구항 윤문 및 생성 완료.")
        
        # 4. State 업데이트를 위한 딕셔너리 반환
        return {"claims_data": refined_claims}