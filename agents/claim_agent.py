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

class ClaimAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3, max_tokens=8192)
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
        
        component_count = len(parsed_data.architecture.components)
        step_count = len(parsed_data.architecture.processing_steps)
        flow_count = len(parsed_data.architecture.data_flows)

        system_prompt = """당신은 한국 특허법에 정통한 [특허 청구범위 작성 AI]입니다.
제공된 발명의 구조화 데이터(Components, Data Flows, Processing Steps)를 바탕으로 특허 청구항을 작성하십시오.

[청구항 작성 핵심 규칙]
1. 카테고리 구성 전략:
   - '시스템', '방법', 'CRM' 3가지 카테고리로 작성합니다.
   - 메인 카테고리 1개를 선정하여 제1항(독립항)을 작성합니다.
   - 종속항은 아래 [발명 규모 정보]에 명시된 구성요소/처리단계 수를 기준으로 빠짐없이 작성합니다.
     각 구성요소의 세부 동작, 각 처리 단계의 구체적 조건, 데이터 흐름의 분기 조건 등을
     각각 별도의 종속항으로 세분화하여 권리범위를 최대한 확보하십시오.
   - 나머지 2개 카테고리에 대해서는 각각 독립항 1개씩 작성합니다.
   - 🎯 [매우 중요] 제1항(독립항)은 단순히 구성요소의 이름만 나열하지 마십시오. 발명의 과제를 해결하기 위한 '필수 구성요소'들과, 이들 간의 '데이터 흐름(Data Flows)' 및 '유기적인 결합/처리 관계'가 구체적으로 드러나도록 한 편의 완결된 문장으로 풍부하게 작성해야 합니다.
   
2. 선행기재 요건 (Antecedent Basis) - 매우 중요:
   - 청구항 내에서 구성요소나 데이터가 **최초로 등장할 때는 '상기'를 붙이지 않습니다.**
   - 이미 등장한 구성요소나 데이터를 **다시 지칭할 때는 반드시 '상기'를 붙여야 합니다.** (예: 입력부; 및 상기 입력부로부터...)
   - 지칭하는 명칭은 Component의 `name`이나 Data Flow의 `data_name`을 정확히 일치시켜야 합니다.

3. 청구항 포맷 및 구두점 규칙:
   - 구성요소나 단계의 나열은 세미콜론(;)으로 구분하고, 마지막 구성요소 앞에는 '및'을 붙입니다.
   - **[주의사항]** 각 청구항의 끝맺음은 입력된 발명의 명칭을 그대로 복사해서 붙이지 마십시오. 청구항의 카테고리에 맞추어 자연스러운 명사형(~하는 시스템, ~하는 방법, ~하는 장치 등)으로 마무리해야 합니다.
   - [시스템항 예시]: A부; 상기 A부와 연결되는 B부; 및 상기 B부에서 전달된 데이터를 처리하는 C부를 포함하는 것을 특징으로 하는 시스템. (또는 장치, 서버 등 발명에 맞는 명칭 사용)
   - [방법항 예시]: A하는 단계; B하는 단계; 및 C하는 단계를 포함하는 것을 특징으로 하는 방법.
   - [종속항 예시]: 제1항에 있어서, 상기 [특정 구성요소]는 ~하는 것을 특징으로 하는 [인용하는 독립항과 동일한 끝맺음 명칭, 예: 시스템].
   - [CRM항 예시]: 하드웨어와 결합되어 제X항의 방법을 실행시키기 위하여 컴퓨터 판독 가능한 기록 매체에 저장된 컴퓨터 프로그램. (제X항은 방법 독립항의 번호를 기재)

4. 종속항(Dependent Claim) 작성 요령:
   - 종속항은 독립항의 구성요소를 단순 반복하거나 재서술하면 절대 안 됩니다.
   - 독립항에 기재된 구성요소의 '구체적인 구현 방식' 또는 '세부 조건'을 새롭게 한정해야 합니다.
   
   [좋은 종속항 예시]
   - 독립항에 "셀프 어텐션 메커니즘을 적용"이 있다면:
     → 종속항: "상기 셀프 어텐션 메커니즘은 스케일드 닷 프로덕트(Scaled Dot-Product) 방식으로 
                쿼리와 키의 내적을 키 차원의 제곱근으로 나누어 소프트맥스 함수를 적용하는 것을 
                특징으로 하는 시스템."
   - 독립항에 "포지셔널 임베딩"이 있다면:
     → 종속항: "상기 포지셔널 임베딩은 사인 및 코사인 함수를 이용하여 각 위치의 순서 정보를 
                인코딩하는 것을 특징으로 하는 시스템."
   - 독립항에 "디코더 네트워크"가 있다면:
     → 종속항: "상기 디코더 네트워크는 이후 위치의 정보를 참조하지 못하도록 마스킹 처리를 
                수행하는 마스크드 셀프 어텐션 모듈을 포함하는 것을 특징으로 하는 시스템."

5. 계층 구조 및 데이터 흐름 반영 규칙 (수정됨):
   - 최상위 구성요소(parent_id=null)는 독립항의 뼈대가 되며, 이 뼈대들이 데이터를 어떻게 주고받는지(Data Flows)를 반드시 독립항에 포함하여 기술하십시오.
   - 하위 구성요소(parent_id가 있는 Component)나 세부적인 처리 단계(Processing Steps)는 해당 상위 구성요소를 구체적으로 한정하는 '종속항'으로 세분화하여 권리범위를 확장하십시오.
"""

        human_prompt = """아래의 구조화된 발명 데이터를 바탕으로 청구항을 작성해 주세요.

[발명의 명칭]
{title}

[해결하고자 하는 과제]
{problem}

[발명 규모 정보] ← 이 수치를 기준으로 종속항 수를 결정하세요
- 구성요소(Components) 수: {component_count}개
- 처리 단계(Processing Steps) 수: {step_count}개  
- 데이터 흐름(Data Flows) 수: {flow_count}개
- 권장 종속항 수: 최소 {min_deps}개 이상

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
            result: ClaimResult = chain.invoke({
                "title": parsed_data.invention_metadata.title,
                "problem": parsed_data.technical_context.problem_to_solve,
                "component_count": component_count,
                "step_count": step_count,
                "flow_count": flow_count,
                "min_deps": max(component_count, step_count),  # 구성요소/단계 수 중 큰 값을 최소 종속항 수로 지정
                "components": json.dumps([c.model_dump() for c in parsed_data.architecture.components], ensure_ascii=False, indent=2),
                "data_flows": json.dumps([f.model_dump() for f in parsed_data.architecture.data_flows], ensure_ascii=False, indent=2),
                "steps": json.dumps([s.model_dump() for s in parsed_data.architecture.processing_steps], ensure_ascii=False, indent=2)
            })
            logger.info("[Claim Agent] 청구항 작성 완료.")
            return {"claims_data": result}
            
        except Exception as e:
            logger.error(f"[Claim Agent] 에러 발생: {str(e)}")
            return {"claims_data": None}
