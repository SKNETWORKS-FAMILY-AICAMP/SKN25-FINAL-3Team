import datetime
from pathlib import Path
from sqlalchemy import Column, String, Integer, Text, ForeignKeyConstraint, DateTime
from agents.consultation.consultation_agent import SessionLocal, Base, engine

# ─────────────────────────────────────────────
# 1. DB 테이블: 도면 전용 (GeneratedDrawing)
# ─────────────────────────────────────────────
class GeneratedDrawing(Base):
    __tablename__ = "generated_drawings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "consultation_idx"],
            ["consulting.user_id", "consulting.consultation_idx"]
        ),
    )
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(String(50), nullable=False)
    consultation_idx = Column(Integer,    nullable=False)
    fig_number       = Column(String(20), nullable=False)
    diagram_type     = Column(String(30), nullable=False)
    diagram_title    = Column(Text,       nullable=True)
    quality_score    = Column(Integer,    nullable=True)
    quality_grade    = Column(String(5),  nullable=True)
    svg_content      = Column(Text,       nullable=True)
    svg_path         = Column(Text,       nullable=True)
    png_path         = Column(Text,       nullable=True)
    created_at       = Column(DateTime,   default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# 2. 도면 결과를 DB에 저장
# ─────────────────────────────────────────────
def save_drawings_to_db(user_id: str, consultation_idx: int, drawing_results: list):
    db = SessionLocal()
    try:
        # 기존 도면 덮어쓰기
        db.query(GeneratedDrawing).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).delete()

        for result in drawing_results:
            svg_content = None
            if result.svg_path and Path(result.svg_path).exists():
                with open(result.svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

            db.add(GeneratedDrawing(
                user_id          = user_id,
                consultation_idx = consultation_idx,
                fig_number       = result.fig_number,
                diagram_type     = result.diagram_type,
                diagram_title    = result.diagram_title,
                quality_score    = result.quality_score,
                quality_grade    = result.quality_grade,
                svg_content      = svg_content,
                svg_path         = result.svg_path,
                png_path         = result.png_path,
            ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

# ─────────────────────────────────────────────
# 3. DB에서 도면 조회
# ─────────────────────────────────────────────
def fetch_drawings_from_db(user_id: str, consultation_idx: int) -> list:
    db = SessionLocal()
    try:
        return db.query(GeneratedDrawing).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).all()
    finally:
        db.close()