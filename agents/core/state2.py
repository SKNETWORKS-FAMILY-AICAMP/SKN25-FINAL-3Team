from typing import TypedDict, Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field

# --- 요약(Summary) 관련 스키마 ---
class Component(BaseModel):
    id: str = Field(description="구성요소의 고유 ID (예: COMP_001)")
    name: str = Field(description="특허 청구항에 들어갈 명사구 형태의 명칭 (예: 디코더 네트워크)")
    type: str = Field(description="구성요소의 속성 (MODULE | STEP | NETWORK | DATABASE 중 택 1)")
    description: str = Field(description="구성요소에 대한 간략한 설명 및 주요 기능")

class DataFlow(BaseModel):
    flow_id: str = Field(description="데이터 흐름의 고유 ID (예: FLOW_001)")
    source: str = Field(description="데이터를 제공하는 주체의 ID (최초 입력인 경우 'INPUT', 그 외에는 COMP_XXX)")
    target: str = Field(description="데이터를 수신하는 대상의 ID (최종 출력인 경우 'OUTPUT', 그 외에는 COMP_XXX)")
    data_name: str = Field(description="전달되는 데이터의 명칭 (빈 값 금지, 문맥을 기반으로 반드시 추론할 것. 예: 음성 텍스트)")

class ProcessingStep(BaseModel):
    step_number: int = Field(description="시간 순서에 따른 실행 단계 번호")
    subject_id: str = Field(description="이 동작을 수행하는 주체 구성요소의 ID (components에 존재하는 id와 일치)")
    action_description: str = Field(description="수행하는 구체적인 동작 (~하는 단계)")
    input_data_ids: List[str] = Field(description="이 단계를 수행하기 위해 필요한 입력 데이터들의 flow_id 리스트")
    output_data_ids: List[str] = Field(description="이 단계를 수행한 결과로 생성/전달되는 데이터들의 flow_id 리스트")

class Architecture(BaseModel):
    components: List[Component] = Field(description="발명을 구성하는 주요 구성요소 리스트")
    data_flows: List[DataFlow] = Field(description="구성요소 간 데이터를 주고받는 흐름 리스트")
    processing_steps: List[ProcessingStep] = Field(description="시계열적 처리 단계 리스트")

class InventionMetadata(BaseModel):
    title: str = Field(description="발명의 명칭")
    category: str = Field(description="발명의 대상 (METHOD | SYSTEM | APPARATUS | PROGRAM 중 택 1)")

class TechnicalContext(BaseModel):
    problem_to_solve: str = Field(description="기존 기술의 한계 및 해결하고자 하는 과제 요약")
    expected_effect: str = Field(description="본 발명을 통해 얻을 수 있는 기술적 효과 요약")

class ParsedInvention(BaseModel):
    invention_metadata: InventionMetadata = Field(description="발명 기본 정보")
    technical_context: TechnicalContext = Field(description="발명의 배경 및 효과")
    architecture: Architecture = Field(description="발명의 핵심 기술 구조 (구성요소, 데이터 흐름, 처리 단계)")

# --- 청구항(Claim) 관련 스키마 ---
class ClaimItem(BaseModel):
    claim_no: int = Field(description="청구항 번호")
    is_dependent: bool = Field(description="종속항 여부 (독립항이면 False)")
    cited_claim_no: List[int] = Field(description="인용하는 청구항 번호 리스트 (독립항인 경우 빈 리스트)")
    category: Literal["방법", "시스템", "CRM"] = Field(description="청구항 카테고리")
    content: str = Field(description="청구항 내용 전문")

class ClaimResult(BaseModel):
    claims: List[ClaimItem] = Field(description="작성된 청구항 리스트")

# --- 심사관(Examiner) 관련 스키마 ---
class RejectionDetail(BaseModel):
    claims: List[int] = Field(description="거절 이유가 발생한 청구항 번호 리스트")
    reason_text: str = Field(description="거절 사유에 대한 상세 설명 텍스트")

class ExaminerResult(BaseModel):
    is_approved: bool = Field(description="전체 청구항 승인 여부 (수정 필요 시 False)")
    rejections: List[RejectionDetail] = Field(description="거절 사유 리스트")
    revision_count: int = Field(description="현재까지 진행된 수정 회차")


# --- 도면 생성용 스키마 ---
class PatentDrawing(BaseModel):
    fig_no: str = Field(description="도면 번호")
    title: str = Field(description="도면 타이틀")
    diagram_type: Literal["BLOCK_DIAGRAM", "FLOWCHART"]
    dot_code: str = Field(description="Graphviz DOT 코드")
    image_path: str = Field(description="생성된 PNG 파일 경로")

class ReferenceMapping(BaseModel):
    component_id: str
    name: str
    numeral: str

class PatentDrawingSpecification(BaseModel):
    drawings: List[PatentDrawing]
    reference_numerals: List[ReferenceMapping]

# =========================================================
# [업데이트] Master Graph State
# =========================================================
class PatentState(TypedDict):
    mock_input_data: Dict[str, Any]
    summary_data: Optional[ParsedInvention]
    claims_data: Optional[ClaimResult]
    examiner_data: Optional[ExaminerResult]
    drawing_spec: Optional[PatentDrawingSpecification]
