from pydantic import BaseModel
from typing import Optional


class ConsultRequest(BaseModel):
    user_input: str
    user_id: str
    session_id: str

class ConsultResponse(BaseModel):
    is_consultation_done: bool
    next_question: str
    invention_flow: Optional[str] = None
    problem: Optional[str] = None
    differentiation: Optional[str] = None
    effect: Optional[str] = None


class PatentSearchRequest(BaseModel):
    invention_flow: str
    problem: str
    differentiation: str
    effect: str

class PatentSearchResponse(BaseModel):
    similar_patents: list
    ipc_codes: list


class ClaimsRequest(BaseModel):
    invention_flow: str
    problem: str
    differentiation: str
    effect: str

class Claim(BaseModel):
    claim_number: int
    claim_type: str             # "method" | "system" | "storage_medium"
    is_independent: bool
    depends_on: int
    content: str

class ClaimsResponse(BaseModel):
    claims: list[Claim]


class ExaminerRequest(BaseModel):
    claims: list[Claim]

class ExaminerResponse(BaseModel):
    is_registerable: bool
    examiner_opinion: str
    examiner_issues: list


class DrawingRequest(BaseModel):
    claims: list[Claim]

class DrawingResponse(BaseModel):
    flowchart_code: str
    system_diagram_code: str


class DescriptionRequest(BaseModel):
    invention_flow: str
    problem: str
    differentiation: str
    effect: str
    flowchart_code: str
    system_diagram_code: str

class DescriptionResponse(BaseModel):
    background: str
    problem_statement: str
    solution: str
    drawing_description: str
    detailed_description: str
