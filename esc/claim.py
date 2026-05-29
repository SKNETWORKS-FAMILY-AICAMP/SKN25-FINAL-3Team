import json
import logging
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from state import PatentState, ClaimResult, ParsedInvention

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ClaimAgent:
    def __init__(self, model_name: str = "gpt-5.4-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.structured_llm = self.llm.with_structured_output(ClaimResult)

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

# ---------------------------------------------------------
# 단독 실행 및 테스트 코드
# ---------------------------------------------------------
if __name__ == "__main__":
    # 제공해주신 Mock 데이터 딕셔너리
    mock_parsed_dict = {
      "invention_metadata": {
        "title": "음성 인식 기반 레시피 추천 시스템",
        "category": "SYSTEM"
      },
      "technical_context": {
        "problem_to_solve": "기존 시스템이 재료의 유통기한을 고려하지 않아, 유통기한 임박 재료의 우선 소진을 반영한 레시피 추천이 어려운 문제",
        "expected_effect": "음식물 쓰레기를 감소시키고 사용자 편의성을 증대시키는 효과"
      },
      "architecture": {
        "components": [
          {
            "id": "COMP_001",
            "name": "음성 입력부",
            "type": "MODULE",
            "description": "사용자의 음성 명령 또는 질의를 수신하는 구성요소"
          },
          {
            "id": "COMP_002",
            "name": "음성 인식 모듈",
            "type": "MODULE",
            "description": "수신된 음성 입력을 텍스트로 변환하는 구성요소"
          },
          {
            "id": "COMP_003",
            "name": "유통기한 대조 모듈",
            "type": "MODULE",
            "description": "변환된 텍스트와 유통기한 데이터베이스를 대조하여 임박 재료 정보를 식별하는 구성요소"
          },
          {
            "id": "COMP_004",
            "name": "레시피 생성 모듈",
            "type": "MODULE",
            "description": "유통기한 임박 재료를 우선 반영하여 레시피를 생성하는 구성요소"
          }
        ],
        "data_flows": [
          {
            "flow_id": "FLOW_001",
            "source": "INPUT",
            "target": "COMP_001",
            "data_name": "사용자 음성 입력"
          },
          {
            "flow_id": "FLOW_002",
            "source": "COMP_001",
            "target": "COMP_002",
            "data_name": "음성 신호"
          },
          {
            "flow_id": "FLOW_003",
            "source": "COMP_002",
            "target": "COMP_003",
            "data_name": "음성 인식 텍스트"
          },
          {
            "flow_id": "FLOW_004",
            "source": "COMP_003",
            "target": "COMP_004",
            "data_name": "유통기한 임박 재료 정보"
          },
          {
            "flow_id": "FLOW_005",
            "source": "COMP_004",
            "target": "OUTPUT",
            "data_name": "추천 레시피"
          }
        ],
        "processing_steps": [
          {
            "step_number": 1,
            "subject_id": "COMP_001",
            "action_description": "사용자 음성 입력을 수신하는 단계",
            "input_data_ids": ["FLOW_001"],
            "output_data_ids": ["FLOW_002"]
          },
          {
            "step_number": 2,
            "subject_id": "COMP_002",
            "action_description": "음성 입력을 텍스트로 변환하는 단계",
            "input_data_ids": ["FLOW_002"],
            "output_data_ids": ["FLOW_003"]
          },
          {
            "step_number": 3,
            "subject_id": "COMP_003",
            "action_description": "변환된 텍스트를 유통기한 DB와 대조하여 임박 재료 정보를 추출하는 단계",
            "input_data_ids": ["FLOW_003"],
            "output_data_ids": ["FLOW_004"]
          },
          {
            "step_number": 4,
            "subject_id": "COMP_004",
            "action_description": "유통기한 임박 재료를 우선 반영하여 레시피를 생성하는 단계",
            "input_data_ids": ["FLOW_004"],
            "output_data_ids": ["FLOW_005"]
          }
        ]
      }
    }

    # 1. 딕셔너리를 Pydantic 객체로 손쉽게 변환 (.model_validate 사용)
    mock_parsed_data = ParsedInvention.model_validate(mock_parsed_dict)

    # 2. 하이브리드 State 초기화 (TypedDict)
    initial_state: PatentState = {
        "mock_input_data": {},
        "summary_data": mock_parsed_data, # Pydantic 객체 주입
        "claims_data": None,
        "examiner_data": None
    }

    # 3. Agent 실행
    agent = ClaimAgent(model_name="gpt-5.4-mini")
    result_update = agent.run(initial_state)

    # 4. 결과 출력
    print("\n" + "="*60)
    print("🌟 [작성된 특허 청구항 (ClaimResult)] 🌟")
    print("="*60)
    
    if result_update.get("claims_data"):
        # claims_data는 Pydantic 객체이므로 속성(.)으로 접근
        claims = result_update["claims_data"].claims
        for claim in claims:
            dep_text = f"(종속항, 인용: {claim.cited_claim_no})" if claim.is_dependent else "(독립항)"
            print(f"\n[제{claim.claim_no}항] {dep_text} - 카테고리: {claim.category}")
            print(f"{claim.content}")
    else:
        print("청구항 작성 실패.")