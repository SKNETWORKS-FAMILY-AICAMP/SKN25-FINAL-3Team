import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from agents.core.state import PatentState, ClaimResult, ClaimItem 

logger = logging.getLogger(__name__)

load_dotenv()

class ClaimRewriteAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1, max_tokens=8192)
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
        rejections = examiner_data.get("rejections", []) if isinstance(examiner_data, dict) else examiner_data.rejections
        for idx, rej in enumerate(rejections, 1):
            claims = rej.get("claims", []) if isinstance(rej, dict) else rej.claims
            reason = rej.get("reason_text", "") if isinstance(rej, dict) else rej.reason_text

            formatted += f"[거절 이유 {idx}]\n"
            formatted += f"- 대상 청구항: {claims}\n"
            formatted += f"- 상세 사유:\n{reason}\n\n"
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

2. 청구항 수 및 구조 유지 (추가):
   - 기존 청구항의 총 개수를 반드시 유지하십시오. 보정 과정에서 청구항을 합치거나 삭제하지 마십시오.
   - 거절 사유가 지적된 청구항만 최소한으로 수정하고, 지적되지 않은 청구항은 원문을 그대로 유지하십시오.
   - 청구항 번호(claim_no), 독립항/종속항 구분(is_dependent), 인용항 번호(cited_claim_no), 카테고리(category)는 절대 변경하지 마십시오.

3. 발명의 실체 및 권리범위 보존:
   - 기재불비를 치유하되, 원래 발명이 가진 고유한 시계열적 데이터 흐름이나 유기적 결합관계의 본질을 훼손하거나 권리범위를 과도하게 축소하지 마십시오.

4. 선행기재 요건 (Antecedent Basis) 및 포맷 준수:
   - 최초로 등장하는 수행 주체나 구성요소에는 '상기'를 붙이지 않으며, 이후 재인용 시에만 '상기'를 엄격하게 적용합니다.
   - 구성요소 나열은 세미콜론(;)으로 구분하고 마지막에 '및'을 붙이는 특허 문언 규격을 유지하십시오.
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


