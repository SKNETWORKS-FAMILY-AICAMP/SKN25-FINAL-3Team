import uuid
import asyncio
import logging
from langsmith import Client
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
langsmith_client = Client()

# 1. 평가 결과를 담을 Pydantic 모델 (2가지 지표 분리)
class ClaimEvaluation(BaseModel):
    formal_compliance_score: int = Field(
        description="상기 등 선행사 명확성 및 종속항 다중인용 규칙 등 형식적 준수성 점수 (1~5)"
    )
    formal_reasoning: str = Field(
        description="형식적 준수성 점수에 대한 구체적인 감점 사유 및 평가 내용"
    )
    scope_completeness_score: int = Field(
        description="핵심 발명 요소 누락 및 불필요한 권리범위 한정(수치, 특정 알고리즘 등) 여부 점수 (1~5)"
    )
    scope_reasoning: str = Field(
        description="권리범위 및 완전성 평가에 대한 구체적인 감점 사유 및 평가 내용"
    )

async def background_llm_judge(run_id: uuid.UUID, input_data: dict, generated_claims: list):
    """
    사용자 모르게 백그라운드에서 청구항을 평가하고 LangSmith에 점수를 기록합니다.
    """
    try:
        # 1. 평가를 위한 텍스트 준비
        claims_text = "\n".join([f"제{c['claim_no']}항: {c['content']}" for c in generated_claims])
        core_tech = input_data.get("core_tech", "")

        # 2. Judge LLM 호출 (gpt-4o 모델 사용)
        judge_llm = ChatOpenAI(model="gpt-4o", temperature=0)
        structured_judge = judge_llm.with_structured_output(ClaimEvaluation)
        
        # 3. 평가 프롬프트 구성 (한국 특허법 기준 명시)
        system_prompt = """당신은 한국 특허청의 깐깐한 수석 심사관입니다.
주어진 원본 [발명 내용]과 AI가 작성한 [생성된 청구항]을 비교하여 아래 2가지 지표를 1~5점(5점이 만점)으로 평가하십시오. 감점 시에는 감점 사유가 발생한 정확한 위치(청구항 번호)와 명확한 사유를 반드시 제공하십시오.

[지표 1: 형식적 준수성 (Formal Compliance)]
- 선행사 명확성: 이전에 언급되지 않은 구성요소에 '상기'나 '상술한'을 붙였는지 감점.
- 종속항 형식 및 인용: "제1항에 있어서, ~하는 것을 특징으로 하는..." 형식을 지켰는가? 한국 특허법의 다중인용규칙(다중종속항이 다른 다중종속항을 인용하는 것 금지)을 위반하지 않았는가?

[지표 2: 권리범위 완전성 (Completeness vs. Scope)]
- 누락 여부(Completeness): 원본 발명의 핵심 기술 사상이 독립항에서 누락되지 않고 모두 기재되었는가?
- 부당한 축소(Scope): 특정 수치("10% 이상")나 특정 알고리즘 이름(예: "ResNet-50") 등으로 불필요하게 한정하여 권리범위가 좁아지지 않았는가? (넓은 상위 개념으로 기재되었는지 우대)
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "[발명 내용]\n{core_tech}\n\n[생성된 청구항]\n{claims_text}")
        ])
        
        # 4. 비동기로 평가 체인 실행
        eval_result = await (prompt | structured_judge).ainvoke({
            "core_tech": core_tech,
            "claims_text": claims_text
        })

        # 5. LangSmith 해당 Trace에 Feedback(평가지표) 분리 기록
        # 정규화를 위해 점수를 5로 나눔 (0.0 ~ 1.0)
        
        # 지표 1: 형식적 준수성 기록
        langsmith_client.create_feedback(
            run_id=run_id,
            key="Formal_Compliance",
            score=eval_result.formal_compliance_score / 5.0,
            comment=eval_result.formal_reasoning
        )
        
        # 지표 2: 권리범위 누락 및 한정 여부 기록
        langsmith_client.create_feedback(
            run_id=run_id,
            key="Scope_Completeness",
            score=eval_result.scope_completeness_score / 5.0,
            comment=eval_result.scope_reasoning
        )
        
        logger.info(f"✅ LangSmith 백그라운드 평가 완료 (Run ID: {run_id})")
        
    except Exception as e:
        # 백그라운드 작업이므로 에러가 나도 메인 서비스(사용자 스트리밍)에는 영향 없음
        logger.error(f"❌ LLM Judge 평가 중 에러 발생: {e}")