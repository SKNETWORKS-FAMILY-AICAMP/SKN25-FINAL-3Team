"""Specification legacy DB 모듈.

현재 LangGraph MVP에서는 agent 간 데이터 전달에 DB를 사용하지 않고 state를 사용합니다.
이 파일은 기존 DB(GeneratedSpecification 등)와의 하위 호환성을 유지하기 위한 코드로,
specification_agent.py 내부에 있던 DB 관련 클래스와 함수를 분리한 것입니다.

에이전트는 이 모듈을 직접 사용하지 않습니다.
DB 저장이 필요한 경우, Graph나 Master가 agent output을 검증하고 state에 병합한 뒤
외부에서 명시적으로 `save_specification_to_db()`를 호출해야 합니다.
"""

from __future__ import annotations

import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKeyConstraint, DateTime

from agents.consultation.consultation_agent import SessionLocal, Base, engine, Consulting, AlgorithmStep
from agents.claim.claim_agent import GeneratedClaim
from agents.drawing.drawing_db import GeneratedDrawing


# ─────────────────────────────────────────────
# DB 테이블: 발명의 설명 (GeneratedSpecification)
# ─────────────────────────────────────────────
class GeneratedSpecification(Base):
    __tablename__ = "generated_specifications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "consultation_idx"],
            ["consulting.user_id", "consulting.consultation_idx"]
        ),
    )
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(String(50), nullable=False)
    consultation_idx = Column(Integer,    nullable=True)
    tech_field        = Column(Text, nullable=True)
    background_art    = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    solution_means   = Column(Text, nullable=True)
    effects          = Column(Text, nullable=True)
    drawing_description     = Column(Text, nullable=True)
    detailed_desc     = Column(Text, nullable=True)
    embodiments      = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)


def init_specification_tables() -> None:
    """DB 테이블 생성을 명시적으로 실행하는 함수."""
    Base.metadata.create_all(bind=engine)


def fetch_data_for_specification(user_id: str, consultation_idx: int) -> dict:
    """DB에서 상담, 청구항, 도면 정보를 조회하여 legacy dict로 반환한다."""
    db = SessionLocal()
    try:
        consult = db.query(Consulting).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).first()
        if not consult:
            raise ValueError(f"상담 내역을 찾을 수 없습니다. (user_id: {user_id}, idx: {consultation_idx})")

        steps = db.query(AlgorithmStep).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).order_by(AlgorithmStep.step_seq).all()

        claim = db.query(GeneratedClaim).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).first()

        drawings = db.query(GeneratedDrawing).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).order_by(GeneratedDrawing.fig_number).all()

        return {
            "problem":    consult.summary_problem or "",
            "solution":   consult.summary_solution or "",
            "difference": consult.summary_difference or "",
            "effect":     consult.summary_effect or "",
            "algorithm_steps": [s.step_content for s in steps],
            "claim_1":         claim.claim_1 if claim else "",
            "dependent_claims": claim.dependent_claims if claim else "",
            "drawings": [
                {"fig_number": d.fig_number, "title": d.diagram_title, "type": d.diagram_type}
                for d in drawings
            ],
        }
    finally:
        db.close()


def build_state_from_legacy_spec_data(data: dict) -> dict:
    """fetch_data_for_specification() 결과를 최소 PatentAgentState 형태로 변환한다."""
    return {
        "consultation": {
            "problem": data.get("problem", ""),
            "solution": data.get("solution", ""),
            "differentiation": data.get("difference", ""),
            "effect": data.get("effect", ""),
            "process_steps": [
                {"order": i+1, "name": f"Step {i+1}", "description": step}
                for i, step in enumerate(data.get("algorithm_steps", []))
            ]
        },
        "claims": {
            "draft_claims": [
                {"claim_no": 1, "type": "independent", "text": data.get("claim_1", "")},
                {"claim_no": 2, "type": "dependent", "text": data.get("dependent_claims", "")}
            ]
        },
        "drawings": {
            "figures": [
                {"fig_no": d.get("fig_number"), "title": d.get("title"), "type": d.get("type")}
                for d in data.get("drawings", [])
            ],
            "reference_numerals": {}
        }
    }


def save_specification_to_db(user_id: str, consultation_idx: int, spec: dict):
    """생성된 명세서 본문 필드만 GeneratedSpecification 테이블에 저장한다.
    주의: 이 함수는 legacy 테이블 호환용이며, specification_agent 내부에서 자동 호출되지 않습니다.
    Agent 실행 후, 결과가 검증되고 state에 병합된 다음에 외부에서 명시적으로 호출해야 합니다.
    """
    db = SessionLocal()
    try:
        existing = db.query(GeneratedSpecification).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).first()

        if existing:
            existing.tech_field         = spec.get("technical_field")
            existing.background_art     = spec.get("background_art")
            existing.problem_statement  = spec.get("problem_to_solve")
            existing.solution_means     = spec.get("means_for_solving")
            existing.effects            = spec.get("effects")
            existing.drawing_description = spec.get("brief_description_of_drawings")
            existing.detailed_desc      = spec.get("detailed_description")
            
            embodiment = spec.get("embodiment_notes")
            existing.embodiments        = "\n".join(embodiment) if isinstance(embodiment, list) else embodiment
            existing.created_at         = datetime.datetime.utcnow()
        else:
            embodiment = spec.get("embodiment_notes")
            db.add(GeneratedSpecification(
                user_id              = user_id,
                consultation_idx     = consultation_idx,
                tech_field           = spec.get("technical_field"),
                background_art       = spec.get("background_art"),
                problem_statement    = spec.get("problem_to_solve"),
                solution_means       = spec.get("means_for_solving"),
                effects              = spec.get("effects"),
                drawing_description  = spec.get("brief_description_of_drawings"),
                detailed_desc        = spec.get("detailed_description"),
                embodiments          = "\n".join(embodiment) if isinstance(embodiment, list) else embodiment,
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
