import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKeyConstraint, DateTime
# consultation_agent에서 DB 연결 객체와 Base를 가져옵니다.
from consultation_agent import SessionLocal, Consulting, AlgorithmStep, DetailElement, Base, engine

# ─────────────────────────────────────────────
# 1. 새로운 DB 테이블: 청구항 전용 (GeneratedClaim)
# ─────────────────────────────────────────────
class GeneratedClaim(Base):
    __tablename__ = "generated_claims"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "consultation_idx"],
            ["consulting.user_id", "consulting.consultation_idx"]
        ),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    consultation_idx = Column(Integer, nullable=False)
    claim_1 = Column(Text, nullable=True)
    dependent_claims = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 앱 실행 시 새로운 테이블이 없다면 자동 생성합니다.
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# 2. DB 데이터 추출 함수 (런팟에 보낼 텍스트 생성)
# ─────────────────────────────────────────────
def fetch_consultation_from_db(user_id: str, consultation_idx: int) -> str:
    """DB에서 상담 내역을 조회하여 프롬프트용 텍스트로 재구성합니다."""
    db = SessionLocal()
    try:
        consult = db.query(Consulting).filter(
            Consulting.user_id == user_id, 
            Consulting.consultation_idx == consultation_idx
        ).first()
        
        if not consult:
            raise ValueError(f"DB에서 해당 상담 내역을 찾을 수 없습니다. (user_id: {user_id}, idx: {consultation_idx})")

        steps = db.query(AlgorithmStep).filter(
            AlgorithmStep.user_id == user_id,
            AlgorithmStep.consultation_idx == consultation_idx
        ).order_by(AlgorithmStep.step_seq).all()

        details = db.query(DetailElement).filter(
            DetailElement.user_id == user_id,
            DetailElement.consultation_idx == consultation_idx
        ).all()

        steps_str = "\n".join([f"  {s.step_seq}단계: {s.step_content}" for s in steps])
        
        detail_dict = {"implementation": [], "parameter": [], "algorithm": [], "optional": [], "error_handling": []}
        for d in details:
            if d.element_type in detail_dict:
                detail_dict[d.element_type].append(d.content)

        def fmt_list(lst): return "\n".join(f"    • {item}" for item in lst) if lst else "    (없음)"

        db_summary = f"""
【 1부 | 독립항 핵심 】
- 문제: {consult.summary_problem}
- 해결: {consult.summary_solution}
- 차별: {consult.summary_difference}
- 효과: {consult.summary_effect}
- 단계:
{steps_str}

【 2부 | 종속항 심화 】
🔧 구현수단: {fmt_list(detail_dict['implementation'])}
📊 데이터: {fmt_list(detail_dict['parameter'])}
⚙️ 핵심로직: {fmt_list(detail_dict['algorithm'])}
➕ 부가기능: {fmt_list(detail_dict['optional'])}
🛡️ 예외처리: {fmt_list(detail_dict['error_handling'])}
"""
        return db_summary
    finally:
        db.close()

# ─────────────────────────────────────────────
# 3. 생성된 청구항을 DB에 저장하는 함수
# ─────────────────────────────────────────────
def save_claims_to_db(user_id: str, consultation_idx: int, claim_1: str, dependent_claims: str):
    """생성된 독립항과 종속항을 DB의 generated_claims 테이블에 저장합니다."""
    db = SessionLocal()
    try:
        # 이미 해당 회차의 청구항이 있는지 확인 (덮어쓰기 로직)
        existing_claim = db.query(GeneratedClaim).filter_by(
            user_id=user_id, consultation_idx=consultation_idx
        ).first()
        
        if existing_claim:
            existing_claim.claim_1 = claim_1
            existing_claim.dependent_claims = dependent_claims
            existing_claim.created_at = datetime.datetime.utcnow()
        else:
            new_claim = GeneratedClaim(
                user_id=user_id,
                consultation_idx=consultation_idx,
                claim_1=claim_1,
                dependent_claims=dependent_claims
            )
            db.add(new_claim)
            
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()