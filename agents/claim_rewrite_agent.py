import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from agents.core.state import PatentState, ClaimResult, ClaimItem 

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ClaimRewriteAgent:
    def __init__(self, model_name: str = "gpt-5.4-mini"):
        # 요청하신 gpt-5.4-mini 모델을 사용하여 정밀한 추론을 수행합니다.
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        # claim.py와 데이터 포맷을 일치시키기 위해 구조화된 출력 스키마를 연결합니다.
        self.structured_llm = self.llm.with_structured_output(
            schema=ClaimResult, 
            method="json_schema", 
            strict=True
        )

    def _format_original_claims(self, claims_data) -> str:
        """기존 청구항 데이터를 프롬프트 입력용 텍스트로 포맷팅"""
        formatted = ""
        for claim in claims_data.claims:
            if claim.is_dependent and claim.cited_claim_no:
                # List[int] 구조이므로 콤마로 연결하여 가독성 확보 (예: 제1항, 제2항)
                citations = ", ".join([f"제{num}항" for num in claim.cited_claim_no])
                dep_text = f"({citations}을 인용하는 종속항)"
            else:
                dep_text = "(독립항)"
                
            formatted += f"[제{claim.claim_no}항] {dep_text} - 카테고리: {claim.category}\n{claim.content}\n\n"
        return formatted.strip()
    

    def _format_rejections(self, examiner_data) -> str:
        """심사관의 거절 사유 데이터를 프롬프트 입력용 텍스트로 포맷팅"""
        formatted = ""
        for idx, rej in enumerate(examiner_data.rejections, 1):
            formatted += f"[거절 이유 {idx}]\n"
            formatted += f"- 대상 청구항: {rej.claims}\n"
            formatted += f"- 상세 사유:\n{rej.reason_text}\n\n"
        return formatted.strip()

    def run(self, state: dict) -> dict:
        """
        기존 청구항(claims_data)과 심사 결과(examiner_data)를 바탕으로
        기재불비 사유를 완벽히 치유한 보정 청구항을 작성하여 반환합니다.
        """
        logger.info("[Claim Rewrite Agent] 청구항 보정 및 재작성 시작...")
        
        claims_data = state.get("claims_data")
        examiner_data = state.get("examiner_data")
        
        if not claims_data or not examiner_data:
            logger.error("보정에 필요한 기존 청구항 또는 심사 결과 데이터가 부족합니다.")
            return {"claims_data": claims_data} # 실패 시 기존 상태 유지

        # 1. 프롬프트에 주입할 입력 데이터 문자열 변환
        original_claims_text = self._format_original_claims(claims_data)
        rejections_text = self._format_rejections(examiner_data)

        system_prompt = """당신은 특허청의 의견제출통지서(거절이유)를 분석하여 완벽한 보정안을 마련하는 [베테랑 특허변리사]입니다.
제시된 [기존 청구범위]와 심사관의 [거절 이유 및 지적 사항]을 바탕으로, 특허법 제42조제4항제2호(명확성 요건)를 완벽하게 만족하도록 청구범위를 재작성하십시오.

[보정 전략 및 핵심 규칙]
1. 거절이유의 완벽한 해소 (가장 중요):
   - 심사관이 지적한 명확성 불비 사유를 기술적으로 정확히 보완해야 합니다.
   - 예컨대, "각 단계를 수행하는 주체가 기재되어 있지 않다"는 지적이 있을 경우, 문맥 및 시스템 구조를 고려하여 각 단계나 구성요소에 명확한 수행 주체(예: '적어도 하나의 프로세서가 ~하는 단계', '상기 프로세서가 ~하는 단계', '제어부가 ~하는 단계' 등)를 명시하여 기재불비를 해소하십시오.
   
2. 발명의 실체 및 권리범위 보존:
   - 기재불비를 치유하되, 원래 발명이 가진 고유한 시계열적 데이터 흐름이나 유기적 결합관계의 본질을 훼손하거나 권리범위를 과도하게 축소하지 마십시오.

3. 선행기재 요건 (Antecedent Basis) 및 포맷 준수:
   - 최초로 등장하는 수행 주체나 구성요소에는 '상기'를 붙이지 않으며, 이후 재인용 시에만 '상기'를 엄격하게 적용합니다.
   - 구성요소 나열은 세미콜론(;)으로 구분하고 마지막에 '및'을 붙이는 특허 문언 규격을 유지하십시오.
   - 청구항 번호(`claim_no`), 독립항/종속항 구분(`is_dependent`), 인용항 번호(`cited_claim_no`), 카테고리(`category`) 정보를 정확하게 유지하거나 필요한 경우 유기적으로 매칭하십시오.
"""

        human_prompt = """아래의 데이터를 바탕으로 지적된 거절 사유를 명확하게 해결한 보정 청구범위(ClaimResult)를 생성해 주세요.

[기존 청구범위]
{original_claims}

[심사관의 거절 이유]
{rejections}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt)
        ])
        
        chain = prompt | self.structured_llm
        
        try:
            # 2. GPT-5.4-mini 추론을 통한 구조화된 보정안 도출
            rewritten_result: ClaimResult = chain.invoke({
                "original_claims": original_claims_text,
                "rejections": rejections_text
            })
            
            logger.info("[Claim Rewrite Agent] 청구항 보정 및 재작성 완료.")
            # 가중치가 수정된 새로운 청구항 데이터를 state에 업데이트
            return {"claims_data": rewritten_result}
            
        except Exception as e:
            logger.error(f"[Claim Rewrite Agent] 에러 발생: {str(e)}")
            return {"claims_data": claims_data} # 에러 발생 시 원래 청구항 유지


# =========================================================
# 단독 실행 및 테스트 코드
# =========================================================
if __name__ == "__main__":
    # 1. 테스트용 기존 파일 스키마 Mocking
    class MockClaimItem:
        def __init__(self, claim_no, content, is_dependent, cited_claim_no, category):
            self.claim_no = claim_no
            self.content = content
            self.is_dependent = is_dependent
            self.cited_claim_no = cited_claim_no  # List[int] 구조 반영
            self.category = category

    class MockClaimResult:
        def __init__(self, claims):
            self.claims = claims

    class MockRejectionDetail:
        def __init__(self, claims, reason_text):
            self.claims = claims
            self.reason_text = reason_text

    class MockExaminerResult:
        def __init__(self, is_approved, rejections, revision_count):
            self.is_approved = is_approved
            self.rejections = rejections
            self.revision_count = revision_count

    # 2. 사용자가 제시한 실제 불합격 상황 데이터 입력
    mock_original_claims = MockClaimResult(claims=[
        MockClaimItem(
            claim_no=1,
            content="거대 언어모델(large language model) 기반 인공지능 모델 시뮬레이션 방법에 있어서, 거대 언어모델을 이용하여 사고(accident)와 연관된 시뮬레이션 시나리오를 생성하는 단계; 상기 생성된 시뮬레이션 시나리오에 기초하여 상기 사고와 연관된 시뮬레이션 환경을 생성하는 단계; 및 상기 생성된 시뮬레이션 환경에 기초하여 인공지능 모델을 시뮬레이션하는 단계를 포함하는, 인공지능 모델 시뮬레이션 방법.",
            is_dependent=False,
            cited_claim_no=[],
            category="방법"
        ),
        MockClaimItem(
            claim_no=2,
            content="제1항에 있어서, 상기 시뮬레이션 시나리오를 생성하는 단계는, 상기 거대 언어모델을 이용하여 상기 사고가 발생한 배경 정보를 생성하는 단계; 상기 거대 언어모델을 이용하여 상기 사고와 연관된 인물 정보를 생성하는 단계; 및 상기 거대 언어모델을 이용하여 상기 배경 정보 및 상기 인물 정보에 기초하여 상기 사고와 연관된 시뮬레이션 시나리오를 생성하는 단계를 포함하는, 인공지능 모델 시뮬레이션 방법.",
            is_dependent=True,
            cited_claim_no=[1],
            category="방법"
        )
    ])

    mock_examiner_data = MockExaminerResult(
        is_approved=False,
        revision_count=1,
        rejections=[
            MockRejectionDetail(
                claims=[1, 2],
                reason_text="각 단계를 수행하는 주체가 기재되어 있지 않아, 각 단계가 어떠한 수행주체에 의해 수행되는지 명확하지 않습니다. 따라서 청구항 1, 2 발명은 명확하고 간결하게 기재되어 있지 않습니다."
            )
        ]
    )

    # 3. Initial State 조립 (PatentState TypedDict 구조와 일치)
    initial_state = {
        "mock_input_data": {},
        "summary_data": None, 
        "claims_data": mock_original_claims,
        "examiner_data": mock_examiner_data
    }

    # 4. Agent 실행
    agent = ClaimRewriteAgent(model_name="gpt-5.4-mini")
    print("⏳ 보정 에이전트를 가동하여 청구항 수정을 시작합니다...")
    
    # 🧪 주의: 실제 실행 시 환경변수에 OPENAI_API_KEY가 로드되어 있어야 합니다.
    result_update = agent.run(initial_state)

    # =========================================================
    # 5. 🌟 [추가됨] 보정 결과 화면 출력 로직
    # =========================================================
    print("\n" + "="*60)
    print("🌟 [보정 및 재작성된 특허 청구항 (ClaimResult)] 🌟")
    print("="*60)
    
    if result_update.get("claims_data"):
        rewritten_claims = result_update["claims_data"].claims
        for claim in rewritten_claims:
            # cited_claim_no가 List[int] 형태이므로 유연하게 다항 인용 처리
            if claim.is_dependent and claim.cited_claim_no:
                citations = ", ".join([f"제{num}항" for num in claim.cited_claim_no])
                dep_text = f"(종속항, 인용: {citations})"
            else:
                dep_text = "(독립항)"
                
            print(f"\n[제{claim.claim_no}항] {dep_text} - 카테고리: {claim.category}")
            print(f"{claim.content}")
    else:
        print("❌ 청구항 보정에 실패했거나 반환된 데이터가 없습니다.")
        
    print("\n" + "="*60)
    
    # 🧪 주의: 실제 실행 시에는 올바른 OPENAI_API_KEY가 환경 변수에 설정되어 있어야 합니다.
    # result_update = agent.run(initial_state)