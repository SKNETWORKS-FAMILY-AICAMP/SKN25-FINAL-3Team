from typing import TypedDict, Optional, List, Literal

# ---------------------------------------------------------
# 1. 요약(Summary) 관련 State
# ---------------------------------------------------------
class Element(TypedDict):
    element_id: int          
    description: str         
    parent_id: Optional[int]


class ConsultationData(TypedDict):
    problems: List[str]      
    elements: List[Element]  
    effects: List[str]       
    user_confirmed: bool # 요약 정리 동의 여부

# ---------------------------------------------------------
# 2. 청구항(Claim) 관련 State
# ---------------------------------------------------------
class ClaimItem(TypedDict):
    claim_no: int
    is_dependent: bool
    cited_claim_no: List[int]  # 인용항이 없으면 빈 리스트 [] 반환
    category: Literal["방법", "시스템", "CRM"]
    content: str

class ClaimResult(TypedDict):
    claims: List[ClaimItem]

# ---------------------------------------------------------
# 3. 심사관(Examiner) 관련 State
# ---------------------------------------------------------
class RejectionDetail(TypedDict):
    claims: List[int]        # 거절 이유에 해당하는 청구항 번호들 (예: [1, 3, 4])
    reason_text: str         # 명확성 요건 위배 이유 구체적 기술 (또는 기존 RejectionReason 객체)

class ExaminerResult(TypedDict):
    is_approved: bool
    rejections: List[RejectionDetail]  # 청구항별 거절 이유 매핑 리스트
    revision_count: int                # 최대 2번 루프 제어용

# ---------------------------------------------------------
# 🌟 Master Graph State
# ---------------------------------------------------------
class PatentState(TypedDict):
    summary_data: ConsultationData  
    claims_data: ClaimResult         
    examiner_data: ExaminerResult