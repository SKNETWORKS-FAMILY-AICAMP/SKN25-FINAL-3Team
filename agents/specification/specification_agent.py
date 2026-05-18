import datetime
import os
from openai import OpenAI
from sqlalchemy import Column, String, Integer, Text, ForeignKeyConstraint, DateTime
from agents.consultation.consultation_agent import SessionLocal, Base, engine, Consulting, AlgorithmStep, DetailElement
from agents.claim.claim_agent import GeneratedClaim
from agents.drawing.drawing_db import GeneratedDrawing

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────────────────────────────────
# 1. DB 테이블: 발명의 설명 (GeneratedSpecification)
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

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# 2. DB에서 명세서 생성에 필요한 데이터 조회
# ─────────────────────────────────────────────
def fetch_data_for_specification(user_id: str, consultation_idx: int) -> dict:
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

# ─────────────────────────────────────────────
# 3. GPT로 발명의 설명 생성
# ─────────────────────────────────────────────
def generate_specification(data: dict) -> dict:
    steps_str = "\n".join(
        f"{i+1}단계: {s}" for i, s in enumerate(data["algorithm_steps"])
    ) if data["algorithm_steps"] else "(없음)"

    drawings_str = "\n".join(
        f"- {d['fig_number']}: {d['title']} ({d['type']})"
        for d in data["drawings"]
    ) if data["drawings"] else "(도면 없음)"

    prompt = f"""당신은 특허 명세서 작성 전문가입니다.
아래 정보를 바탕으로 특허 명세서의 각 항목을 한국 특허 양식에 맞게 작성해 주세요.

【 상담 내용 】
- 문제: {data['problem']}
- 해결방법: {data['solution']}
- 차별성: {data['difference']}
- 효과: {data['effect']}
- 알고리즘 단계:
{steps_str}

【 청구항 】
독립항(제1항): {data['claim_1']}
종속항: {data['dependent_claims']}

【 생성된 도면 목록 】
{drawings_str}

위 정보를 토대로 아래 8개 항목을 각각 작성해 주세요.
JSON 형식으로 반환하되, 키는 반드시 아래와 같이 사용하세요:
- "tech_field": 기술분야 (2~3문장)
- "background_art": 배경기술 (3~5문장)
- "problem_statement": 해결하고자 하는 과제 (상담 내용의 문제점 기반, 3~5문장)
- "solution_means": 과제의 해결수단 (청구항 기반, 독립항과 종속항을 포함하여 3~5문장)
- "effects": 발명의 효과 (상담 내용의 효과 기반, 3~5문장)
- "drawing_description": 도면의 간단한 설명 (도면 목록의 각 도면을 한 줄씩 설명)
- "detailed_desc": 발명을 실시하기 위한 구체적인 내용 (10문장 이상)
- "embodiments": 실시예 (5문장 이상)

JSON 외 다른 텍스트는 출력하지 마세요."""

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    import json
    return json.loads(response.choices[0].message.content)

# ─────────────────────────────────────────────
# 4. 생성된 명세서를 DB에 저장
# ─────────────────────────────────────────────
def save_specification_to_db(user_id: str, consultation_idx: int, spec: dict):
    db = SessionLocal()
    try:
        existing = db.query(GeneratedSpecification).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).first()

        if existing:
            existing.tech_field         = spec.get("tech_field")
            existing.background_art     = spec.get("background_art")
            existing.problem_statement  = spec.get("problem_statement")
            existing.solution_means     = spec.get("solution_means")
            existing.effects            = spec.get("effects")
            existing.drawing_description = spec.get("drawing_description")
            existing.detailed_desc      = spec.get("detailed_desc")
            existing.embodiments        = spec.get("embodiments")
            existing.created_at         = datetime.datetime.utcnow()
        else:
            db.add(GeneratedSpecification(
                user_id              = user_id,
                consultation_idx     = consultation_idx,
                tech_field           = spec.get("tech_field"),
                background_art       = spec.get("background_art"),
                problem_statement    = spec.get("problem_statement"),
                solution_means       = spec.get("solution_means"),
                effects              = spec.get("effects"),
                drawing_description  = spec.get("drawing_description"),
                detailed_desc        = spec.get("detailed_desc"),
                embodiments          = spec.get("embodiments"),
            ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
