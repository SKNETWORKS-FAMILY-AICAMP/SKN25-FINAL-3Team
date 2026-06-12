import json
import logging
from dotenv import load_dotenv
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
#from agents.core.state import PatentState, ClaimResult, ClaimItem, Element
from agents.core.state import PatentState, ClaimResult, ParsedInvention

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# def parent_map_desc(element_map: Dict[int, Element], parent_id: int) -> str:
#     """부모 구성요소의 명칭을 정제해서 가져오는 헬퍼 함수"""
#     full_desc = element_map[parent_id]['description']

#     # 프롬프트나 로직에서 명칭만 자르기 위한 임시 파싱 (실무에서는 더 정교한 명사 추출 필요)
#     return full_desc.split("하는")[-1].strip() if "하는" in full_desc else full_desc[:15]

# def generate_claims_structure(consultation: ConsultationData) -> ClaimResult:
#     """
#     [Rule-Based] 요약 데이터를 바탕으로 특허법적 계층 구조를 가진 청구항 뼈대를 생성합니다.
#     """
#     elements = consultation["elements"]
#     problems = consultation.get("problems", [])
#     effects = consultation.get("effects", [])

#     #element_map: Dict[int, Element] = {el["element_id"]: el for el in elements}
#     element_map = {}
#     for el in elements:
#         key = el["element_id"]
#         element_map[key] = el
#     el_to_claim_map: Dict[int, int] = {}
    
#     claims_list: List[ClaimItem] = []
#     current_claim_no = 1

#     # [STEP 1] 독립항 생성 (parent_id가 없는 최상위 요소)
#     #top_elements = [el for el in elements if el.get("parent_id") is None]
#     top_elements = []
#     for el in elements:
#         if el.get("parent_id") is None:
#             top_elements.append(el)
    
#     for el in top_elements:
#         el_id = el["element_id"]
#         el_to_claim_map[el_id] = current_claim_no
        
#         category = "시스템" if "시스템" in el["description"] else "방법"
#         problem_text = problems[0] if problems else ""
#         effect_text = effects[0] if effects else ""
        
#         content = (
#             f"[해결과제: {problem_text}]를 해결하기 위한 {el['description']}로서, "
#             f"상기 {el['description']}의 세부 메커니즘을 포함하여 [기대효과: {effect_text}]를 특징으로 하는 {category}."
#         )
        
#         claims_list.append({
#             "claim_no": current_claim_no,
#             "is_dependent": False,
#             "cited_claim_no": [],
#             "category": category,
#             "content": content
#         })
#         current_claim_no += 1

#     # [STEP 2] 종속항 생성 (parent_id가 존재하는 세부 요소)
#     #sub_elements = [el for el in elements if el.get("parent_id") is not None]
#     sub_elements = []
#     for el in elements:
#         if el.get("parent_id") is not None:
#             sub_elements.append(el)

#     for el in sub_elements:
#         el_id = el["element_id"]
#         parent_id = el["parent_id"]
#         parent_claim_no = el_to_claim_map.get(parent_id)
        
#         if parent_claim_no is not None:
#             el_to_claim_map[el_id] = current_claim_no
#             parent_claim = next((c for c in claims_list if c["claim_no"] == parent_claim_no), None)
#             category = parent_claim["category"]
            
#             content = (
#                 f"제{parent_claim_no}항에 있어서, "
#                 f"상기 {parent_map_desc(element_map, parent_id)}는, "
#                 f"{el['description']}을(를) 더 포함하는 것을 특징으로 하는 {category}."
#             )
            
#             claims_list.append({
#                 "claim_no": current_claim_no,
#                 "is_dependent": True,
#                 "cited_claim_no": [parent_claim_no],
#                 "category": category,
#                 "content": content
#             })
#             current_claim_no += 1

#     return {"claims": claims_list}

# class ClaimGenerationAgent:
#     def __init__(self, model_name: str = "gpt-4o"):
#         # 모델명을 외부에서 주입받을 수 있도록 수정 (유연성 확보)
#         # 청구항 구조를 건드리지 않고 문장만 다듬는 것이라 gpt-4o 또는 gpt-4o-mini 모두 적합합니다.
#         self.llm = ChatOpenAI(model=model_name, temperature=0.2)

#     def run(self, state: PatentState) -> Dict[str, Any]:
#         """
#         LangGraph 노드 함수: 요약 데이터를 읽어 청구항을 생성(윤문)하고 반환합니다.
#         """
#         logger.info("[Claim Agent] 구조화된 출력을 활용한 청구항 생성 시작...")
        
#         consultation_data = state.get("summary_data")
#         if not consultation_data:
#             logger.error("State에 summary_data가 존재하지 않습니다.")
#             raise ValueError("State에 summary_data가 존재하지 않습니다. 요약 노드를 먼저 확인하세요.")
        
#         # 1. 뼈대 생성 (Rule-based)
#         base_claim_structure = generate_claims_structure(consultation_data)
        
#         # 2. 프롬프트 작성
#         system_prompt = (
#             "당신은 대한민국의 베테랑 특허출원 전문 변리사입니다.\n"
#             "제공된 청구항 JSON 구조의 'claim_no', 'is_dependent', 'cited_claim_no', 'category' 데이터는 "
#             "특허법적 인용 관계를 고려하여 철저히 계산된 뼈대이므로 절대로 수정하거나 가공하지 마십시오.\n\n"
#             "당신의 임무는 오직 각 청구항의 'content' 문자열을 대한민국 특허 실무 규정에 맞는 "
#             "세련되고 유기적인 청구범위 문체(예: ~을 특징으로 하는 방법.)로 확장하고 다듬는 것입니다."
#         )
        
#         user_prompt = (
#             f"아래의 청구항 뼈대 구조를 바탕으로 content 영역의 문장을 변리사답게 다듬어 주세요.\n"
#             f"입력 데이터: {json.dumps(base_claim_structure, ensure_ascii=False)}"
#         )
        
#         # 3. LLM 호출 및 Pydantic(TypedDict) 포맷 강제
#         structured_llm = self.llm.with_structured_output(ClaimResult)
        
#         refined_claims: ClaimResult = structured_llm.invoke([
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ])
        
#         logger.info("[Claim Agent] 청구항 윤문 및 생성 완료.")
        
#         # 4. State 업데이트를 위한 딕셔너리 반환
#         return {"claims_data": refined_claims}
    

class ClaimAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3, max_tokens=4096)
        self.structured_llm = self.llm.with_structured_output(ClaimResult,method="json_schema", 
            strict=True)

    def run(self, state: PatentState) -> dict:
        """
        TypedDict인 state에서 summary_data(Pydantic 객체)를 꺼내 
        특허 청구항(ClaimResult)을 작성하여 반환합니다.
        """
        logger.info("[Claim Agent] 청구항 작성 시작...")
        
        # 1. State(TypedDict)에서 Pydantic 객체 꺼내기
        parsed_data: ParsedInvention = state.get("summary_data")
        
        if not parsed_data:
            logger.error("파싱된 발명 데이터(summary_data)가 없습니다.")
            return {"claims_data": None}

        system_prompt = """당신은 한국 특허법에 정통한 [특허 청구범위 작성 AI]입니다.
제공된 발명의 구조화 데이터(Components, Data Flows, Processing Steps)를 바탕으로 특허 청구항을 작성하십시오.

[청구항 작성 핵심 규칙]
[청구항 작성 핵심 규칙]
1. 카테고리 구성 전략:
   - '시스템', '방법', 'CRM' 3가지 카테고리로 작성합니다.
   - 메인 카테고리 1개를 선정하여 제1항(독립항)을 작성하고, 이에 대한 종속항들을 2~3개 작성합니다.
   - 나머지 2개 카테고리에 대해서는 각각 독립항 1개씩만 작성합니다 (종속항 작성 금지).
   
2. 선행기재 요건 (Antecedent Basis) - 매우 중요:
   - 청구항 내에서 구성요소나 데이터가 **최초로 등장할 때는 '상기'를 붙이지 않습니다.**
   - 이미 등장한 구성요소나 데이터를 **다시 지칭할 때는 반드시 '상기'를 붙여야 합니다.** (예: 입력부; 및 상기 입력부로부터...)
   - 지칭하는 명칭은 Component의 `name`이나 Data Flow의 `data_name`을 정확히 일치시켜야 합니다.

3. 청구항 포맷 및 구두점 규칙:
   - 구성요소나 단계의 나열은 세미콜론(;)으로 구분하고, 마지막 구성요소 앞에는 '및'을 붙입니다.
   - [시스템항 예시]: A부; 상기 A부와 연결되는 B부; 및 상기 B부에서 전달된 데이터를 처리하는 C부를 포함하는 [발명의 명칭].
   - [방법항 예시]: A하는 단계; B하는 단계; 및 C하는 단계를 포함하는 [발명의 명칭].
   - [종속항 예시]: 제1항에 있어서, 상기 [특정 구성요소]는 ~하는 것을 특징으로 하는 [발명의 명칭].
   - [CRM항 예시]: 하드웨어와 결합되어 제X항의 방법을 실행시키기 위하여 컴퓨터 판독 가능한 기록 매체에 저장된 컴퓨터 프로그램. (제X항은 방법 독립항의 번호를 기재)

4. 종속항(Dependent Claim) 작성 요령:
   - 종속항은 단순히 구성을 반복하는 것이 아니라, 특정 Component의 구체적인 동작 방식, Data Flow의 조건, 또는 해결하고자 하는 과제를 달성하기 위한 구체적인 수단을 한정해야 합니다.
"""

        human_prompt = """아래의 구조화된 발명 데이터를 바탕으로 청구항을 작성해 주세요.

[발명의 명칭]
{title}

[해결하고자 하는 과제]
{problem}

[구성요소 (Components)]
{components}

[데이터 흐름 (Data Flows)]
{data_flows}

[처리 단계 (Processing Steps)]
{steps}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.structured_llm
        
        try:
            # Pydantic 객체를 통째로 JSON 문자열로 변환하여 프롬프트에 주입
            result: ClaimResult = chain.invoke({
                "title": parsed_data.invention_metadata.title,
                "problem": parsed_data.technical_context.problem_to_solve,
                "components": json.dumps([c.model_dump() for c in parsed_data.architecture.components], ensure_ascii=False, indent=2),
                "data_flows": json.dumps([f.model_dump() for f in parsed_data.architecture.data_flows], ensure_ascii=False, indent=2),
                "steps": json.dumps([s.model_dump() for s in parsed_data.architecture.processing_steps], ensure_ascii=False, indent=2)
            })
            
            logger.info("[Claim Agent] 청구항 작성 완료.")
            return {"claims_data": result}
            
        except Exception as e:
            logger.error(f"[Claim Agent] 에러 발생: {str(e)}")
            return {"claims_data": None}
