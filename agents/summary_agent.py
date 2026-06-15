import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from agents.core.state import PatentState, ParsedInvention

logger = logging.getLogger(__name__)

class SummaryAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0, max_tokens=4096)
        self.structured_llm = self.llm.with_structured_output(ParsedInvention)

    def run(self, state: PatentState) -> dict:
        """
        State의 mock_input_data를 읽어 파싱을 수행하고,
        그 결과를 summary_data로 반환합니다.
        """
        logger.info("[Summary Agent] 발명 데이터 파싱 시작...")
        input_data = state.get("mock_input_data", {})
        
        if not input_data:
            logger.error("Mock Data가 제공되지 않았습니다.")
            return {"summary_data": None}
            
        system_prompt = """너는 특허 청구항 자동 작성을 위한 [특허 정보 파싱 전문가]이다.
사용자가 입력한 발명 텍스트를 분석하여 제공된 JSON 스키마에 맞게 구조화 데이터를 생성하라.

[절대 원칙 - 정보 손실 금지]
- 입력 텍스트의 내용을 절대 요약하거나 생략하지 마라.
- 발명 텍스트에 등장하는 모든 구성요소, 입력값, 처리 단계, 데이터 흐름을 빠짐없이 추출하라.
- 하나의 문장에 여러 동작이 있다면 각각을 별도의 ProcessingStep으로 분리하라.
- 하나의 구성요소에 여러 역할이 있다면 각 역할을 별도의 DataFlow로 표현하라.

[구성요소 추출 기준]
- 발명 텍스트에서 명사구(~부, ~모듈, ~네트워크, ~장치, ~수단)로 표현되는 모든 요소를 Component로 추출하라.
- 입력값으로 명시된 데이터 항목 각각을 별도의 DataFlow로 추출하라.
  예) "원본 문장", "토큰 단위 정보", "포지셔널 임베딩", "이미 생성된 출력 토큰" → 각각 별도 FLOW

[ID 기반 관계 매핑]
- 모든 구성요소는 'COMP_001', 'COMP_002' 형태의 고유 ID를 가져야 한다.
- 모든 데이터 흐름은 'FLOW_001', 'FLOW_002' 형태의 고유 ID를 가져야 한다.
- ProcessingStep의 subject_id는 반드시 Component에 존재하는 ID를 참조해야 한다.
- ProcessingStep의 input_data_ids, output_data_ids는 반드시 DataFlow에 존재하는 ID를 참조해야 한다.

[계층 관계 설정]
- 상위 시스템에 포함되는 하위 모듈은 parent_id에 상위 구성요소의 ID를 반드시 기재하라.
- 예: 신경망 시스템(COMP_001) 안에 디코더 네트워크(COMP_002)가 포함된다면
      COMP_002의 parent_id = "COMP_001"
- 최상위 구성요소만 parent_id를 null로 설정하라.

[경계 설정]
- 시스템의 최초 입력 데이터 소스는 'INPUT', 최종 출력 타겟은 'OUTPUT'이라는 예약어를 사용하라.

[명사구 및 동사구 정제]
- Component의 name은 "~부", "~모듈", "~네트워크" 등의 특허청구범위용 명사구로 정제하라.
- ProcessingStep의 action_description은 "~하는 단계" 형식으로 정제하라.
"""

        human_prompt = """아래의 발명 신고서 데이터를 분석하여 구조화해라.
입력된 모든 구성요소, 입력값, 처리방식, 출력값을 하나도 빠뜨리지 말고 추출하라.

[발명의 명칭]
{title}

[기존 기술의 문제점]
{prior_art_problem}

[해결하고자 하는 과제]
{problem_to_solve}

[핵심 기술 구성 (Solution)] ← 이 섹션의 모든 항목을 빠짐없이 구성요소/처리단계/데이터흐름으로 변환하라
{core_tech}

[기대 효과]
{expected_effect}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.structured_llm
        
        try:
            result: ParsedInvention = chain.invoke({
                "title": input_data.get("title", "기재되지 않음"),
                "prior_art_problem": input_data.get("prior_art_problem", "기재되지 않음"),
                "problem_to_solve": input_data.get("problem_to_solve", "기재되지 않음"),
                "core_tech": input_data.get("core_tech", "핵심 구성 없음"),
                "expected_effect": input_data.get("expected_effect", "기재되지 않음")
            })
            
            logger.info("[Summary Agent] 파싱 완료.")
            return {"summary_data": result}
            
        except Exception as e:
            logger.error(f"[Summary Agent] 에러 발생: {str(e)}")
            return {"summary_data": None}