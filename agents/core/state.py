from typing import TypedDict, Optional, List, Literal, Annotated

# ---------------------------------------------------------
# 1. 요약(Summary) 관련 State
# ---------------------------------------------------------
class Component(TypedDict):
    id: Annotated[str, "구성요소의 고유 ID (예: COMP_001)"]
    name: Annotated[str, "특허 청구항에 들어갈 명사구 형태의 명칭 (예: 디코더 네트워크)"]
    type: Annotated[str, "구성요소의 속성 (MODULE | STEP | NETWORK | DATABASE 중 택 1)"]
    description: Annotated[str, "구성요소에 대한 간략한 설명 및 주요 기능"]

class DataFlow(TypedDict):
    flow_id: Annotated[str, "데이터 흐름의 고유 ID (예: FLOW_001)"]
    source: Annotated[str, "데이터를 제공하는 주체의 ID (최초 입력인 경우 'INPUT', 그 외에는 COMP_XXX)"]
    target: Annotated[str, "데이터를 수신하는 대상의 ID (최종 출력인 경우 'OUTPUT', 그 외에는 COMP_XXX)"]
    data_name: Annotated[str, "전달되는 데이터의 명칭 (예: 포지셔널 임베딩)"]

class ProcessingStep(TypedDict):
    step_number: Annotated[int, "시간 순서에 따른 실행 단계 번호"]
    subject_id: Annotated[str, "이 동작을 수행하는 주체 구성요소의 ID (components에 존재하는 id와 일치)"]
    action_description: Annotated[str, "수행하는 구체적인 동작 (~하는 단계)"]
    input_data_ids: Annotated[List[str], "이 단계를 수행하기 위해 필요한 입력 데이터들의 flow_id 리스트"]
    output_data_ids: Annotated[List[str], "이 단계를 수행한 결과로 생성/전달되는 데이터들의 flow_id 리스트"]

class Architecture(TypedDict):
    components: Annotated[List[Component], "발명을 구성하는 주요 구성요소 리스트"]
    data_flows: Annotated[List[DataFlow], "구성요소 간 데이터를 주고받는 흐름 리스트"]
    processing_steps: Annotated[List[ProcessingStep], "시계열적 처리 단계 리스트"]

class InventionMetadata(TypedDict):
    title: Annotated[str, "발명의 명칭"]
    category: Annotated[str, "발명의 대상 (METHOD | SYSTEM | APPARATUS | PROGRAM 중 택 1)"]

class TechnicalContext(TypedDict):
    problem_to_solve: Annotated[str, "기존 기술의 한계 및 해결하고자 하는 과제 요약"]
    expected_effect: Annotated[str, "본 발명을 통해 얻을 수 있는 기술적 효과 요약"]

class ParsedInvention(TypedDict):
    invention_metadata: Annotated[InventionMetadata, "발명 기본 정보"]
    technical_context: Annotated[TechnicalContext, "발명의 배경 및 효과"]
    architecture: Annotated[Architecture, "발명의 핵심 기술 구조 (구성요소, 데이터 흐름, 처리 단계)"]

# ---------------------------------------------------------
# 2. 청구항(Claim) 관련 State
# ---------------------------------------------------------
class ClaimItem(TypedDict):
    claim_no: int
    is_dependent: bool
    cited_claim_no: List[int]  
    category: Literal["방법", "시스템", "CRM"]
    content: str

class ClaimResult(TypedDict):
    claims: List[ClaimItem]

# ---------------------------------------------------------
# 3. 심사관(Examiner) 관련 State
# ---------------------------------------------------------
class RejectionDetail(TypedDict):
    claims: List[int]        
    reason_text: str         

class ExaminerResult(TypedDict):
    is_approved: bool
    rejections: List[RejectionDetail] 
    revision_count: int               

# ---------------------------------------------------------
# 🌟 Master Graph State
# ---------------------------------------------------------
class PatentState(TypedDict):
    mock_input_data: dict  # 사용자 입력을 Mock Data로 받기 위한 필드
    summary_data: Optional[ParsedInvention]
    claims_data: Optional[ClaimResult]        
    examiner_data: Optional[ExaminerResult]