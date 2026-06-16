# import logging
# from typing import Dict, Any
# from langchain_openai import ChatOpenAI
# from agents.core.state import PatentState, ClaimResult, ExaminerResult

# # 실무 환경을 위한 로깅 설정
# logger = logging.getLogger(__name__)


# class ExaminerAgent:
#     def __init__(self, model_name: str = "gpt-4o"):
#         self.llm = ChatOpenAI(model=model_name, temperature=0.0)

#     def _format_claims_to_text(self, claims_result: ClaimResult) -> str:
#         """
#         LLM 심사관이 청구항 간의 구조와 인용 관계를 한눈에 파악할 수 있도록 
#         JSON 데이터를 읽기 편한 텍스트 전문으로 정제하는 헬퍼 함수입니다.
#         """
#         text_lines = []
#         for c in claims_result.get("claims", []):
#             prefix = "[종속항]" if c.get("is_dependent") else "[독립항]"
#             text_lines.append(f"{prefix} 청구항 {c.get('claim_no')} ({c.get('category')})")
#             if c.get("is_dependent"):
#                 text_lines.append(f"인용 대상 청구항 번호들: {c.get('cited_claim_no', [])}")
#             text_lines.append(f"내용: {c.get('content')}\n")
#         return "\n".join(text_lines)

#     def run(self, state: PatentState) -> Dict[str, Any]:
#         """
#         LangGraph 노드 함수: 작성된 청구항을 검토하여 특허법 위배 여부를 심사합니다.
#         """
#         logger.info("[Examiner Agent] 특허 청구범위 심사 시작...")

#         claims_data = state.get("claims_data")

#         # 1. State에서 이전 노드(ClaimAgent)가 만든 청구항 데이터 가져오기
#         claims_data: ClaimResult = state.get("claims_data")
#         if not claims_data or "claims" not in claims_data:
#             logger.error("State에 claims_data가 존재하지 않습니다.")
#             raise ValueError("State에 claims_data가 존재하지 않습니다. 청구항 생성 노드를 먼저 실행하세요.")

#         # 2. 심사를 위한 텍스트 변환
#         claims_text_for_review = self._format_claims_to_text(claims_data)

#         # 3. 심사관 프롬프트 (특허법 기반 Few-Shot 역할)
#         system_prompt = (
#             "당신은 대한민국 특허청의 엄격한 베테랑 특허심사관입니다.\n"
#             "입력된 청구범위를 검토하여 다음 '2가지 법적 요건'만 집중적으로 심사해 주세요.\n\n"
#             "=== 심사 기준 ===\n"
#             "1. 특허법 제42조 제4항 제2호 (명확성 요건):\n"
#             "   - 청구항에 기재된 발명이 모호하거나 불명확하여 발명의 구성을 파악할 수 없는 경우 거절.\n"
#             "   - 특히, 앞서 선언되지 않은 구성요소를 '상기 [구성요소]'라고 인용하는 경우(선행 명사 부존재) 기재불량으로 적발할 것.\n"
#             "2. 특허법 시행령 제4조 제4항 (다중인용항의 다중인용항 인용 금지):\n"
#             "   - 2개 이상의 청구항을 인용하는 청구항을 '다중인용항'이라 합니다.\n"
#             "   - 어떤 청구항이 인용하는 대상 중에 '이미 다중인용항인 청구항'이 단 하나라도 포함되어 있다면, 이는 '다다중 인용'으로 무조건 거절해야 합니다.\n\n"
#             "=== 반환 형식 ===\n"
#             "반드시 제공된 ExaminerResult 스키마 규격을 준수하여 응답하세요."
#         )

#         # 4. 구조화된 출력 (Structured Output) 강제 적용
#         structured_llm = self.llm.with_structured_output(ExaminerResult)

#         # 5. LLM 심사 진행
#         examination_output: ExaminerResult = structured_llm.invoke([
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"이하의 청구범위를 엄격하게 심사하십시오:\n\n{claims_text_for_review}"}
#         ])

#         # 6. 루프 제어용 State 관리 (revision_count)
#         # 이전 심사 기록이 있다면 가져오고, 첫 심사라면 0으로 세팅합니다.
#         examiner_state = state.get("examiner_data") or {}
#         current_count = examiner_state.get("revision_count", 0)

#         if not examination_output.get("is_approved"):
#             examination_output["revision_count"] = current_count + 1
#             logger.warning(f"[Examiner Agent] 거절 이유 발견! (현재 누적 수정 횟수: {examination_output['revision_count']})")
#         else:
#             examination_output["revision_count"] = current_count
#             logger.info("[Examiner Agent] 모든 청구항 심사 통과! (최종 승인)")

#         return {"examiner_data": examination_output}