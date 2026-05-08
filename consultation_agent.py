import os
import json
import shutil
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from openai import OpenAI

from document_utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_hwp,
    extract_images_from_pdf,
    encode_image_to_base64
)

load_dotenv()

# ─────────────────────────────────────────────
# DB 연결
# ─────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user     = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host     = os.getenv("DB_HOST")
    db_port     = os.getenv("DB_PORT", "5432")
    db_name     = os.getenv("DB_NAME")
    if all([db_user, db_password, db_host, db_name]):
        if "supabase.com" in db_host:
            project_id = db_name.split(".")[-1] if "." in db_name else db_name
            db_user    = f"{db_user}.{project_id}" if project_id not in db_user else db_user
            db_name    = "postgres"
        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

Base = declarative_base()

# ─────────────────────────────────────────────
# DB 모델
# ─────────────────────────────────────────────

class Consulting(Base):
    __tablename__ = "consulting"
    user_id            = Column(String(50), primary_key=True)
    consultation_idx   = Column(Integer,    primary_key=True)
    raw_chat_log       = Column(JSON)
    uploaded_file_path = Column(Text)
    summary_problem    = Column(Text)
    summary_solution   = Column(Text)
    summary_difference = Column(Text)
    summary_effect     = Column(Text)
    steps   = relationship("AlgorithmStep", back_populates="consultation", cascade="all, delete-orphan")
    details = relationship("DetailElement",  back_populates="consultation", cascade="all, delete-orphan")


class AlgorithmStep(Base):
    __tablename__ = "algorithm_steps"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "consultation_idx"],
            ["consulting.user_id", "consulting.consultation_idx"]
        ),
    )
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(String(50), nullable=False)
    consultation_idx = Column(Integer,    nullable=False)
    step_seq         = Column(Integer,    nullable=False)
    step_content     = Column(Text,       nullable=False)
    consultation = relationship("Consulting", back_populates="steps")


class DetailElement(Base):
    __tablename__ = "detail_elements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "consultation_idx"],
            ["consulting.user_id", "consulting.consultation_idx"]
        ),
    )
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(String(50), nullable=False)
    consultation_idx = Column(Integer,    nullable=False)
    element_type     = Column(String(30), nullable=False)
    seq              = Column(Integer,    nullable=False)
    content          = Column(Text,       nullable=False)
    consultation = relationship("Consulting", back_populates="details")


engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ─────────────────────────────────────────────
# 프롬프트 상수
# ─────────────────────────────────────────────

PHASE1_SYSTEM = "당신은 정밀한 특허 분석가입니다. 지시한 JSON 외에 어떤 텍스트도 출력하지 마세요."

PHASE1_EXTRACT_PROMPT = """
당신은 특허 전문 변리사 에이전트입니다. 사용자의 답변에서 발명의 4대 핵심 요소를 정밀 추출하세요.

[현재 변리사가 사용자에게 묻고 있는 항목]: {current_asking}
(사용자의 답변은 이 항목에 대한 응답일 가능성이 매우 높습니다. 모호하더라도 해당 필드에 우선 반영하세요.)

현재 파악된 정보:
- 문제점: {problem}
- 해결방법: {solution}
- 차별성: {differentiation}
- 기대효과: {effect}

사용자 입력: {user_input}

[추출 규칙]
- 사용자가 명시적으로 말하지 않은 내용은 절대 추측해서 채우지 마세요(null로 두기).
- 알고리즘 단계는 별도로 수집하므로 여기서는 추출하지 않습니다.
- 결과는 반드시 아래 JSON 형식으로만 응답하세요.

{{
    "problem": "문자열 또는 null",
    "solution": "문자열 또는 null",
    "differentiation": "문자열 또는 null",
    "effect": "문자열 또는 null"
}}
"""

POLISH_PROMPT = """
당신은 전문 변리사입니다. 사용자가 구두로 설명한 거친 표현들을 특허 명세서용 전문 용어로 정제해 주세요.
오타 수정, 문어체 변환, 용어 공식화에 집중하세요. 내용은 변경하지 마세요.

항목: {field_name}
원문: {raw_text}

정제된 텍스트만 출력하세요.
"""

PHASE2_QUESTION = """
독립항 핵심 내용 확인이 완료되었습니다. 🎉
이제 청구항을 더욱 탄탄하게 만들 심화 정보를 여쭤볼게요.
아시는 항목만 편하게 답해 주시면 됩니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 1. 구체적인 구현 수단 (예: YOLO v8, Python 등)
📊 2. 데이터 파라미터 (예: 사용자 알레르기 정보 등)
⚙️ 3. 핵심 로직 및 수식 (예: 스코어링 가중치 함수 등)
➕ 4. 부가적/선택적 기능 (예: 자동 주문 연동 등)
🛡️ 5. 예외 처리 (예: 인식 실패 시 수동 입력 UI 등)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
모르시는 항목은 '없음' 또는 패스라고 하셔도 됩니다.
"""

PHASE2_EXTRACT_PROMPT = """
당신은 특허 전문 변리사입니다. 발명가의 답변에서 심화 정보를 추출하세요. (JSON 응답)

발명 맥락 (참고):
- 해결방법: {solution}
- 알고리즘: {algorithm_steps}

사용자 입력: {user_input}

[추출 항목]
1. implementations   : 구체적인 구현 수단
2. parameters        : 데이터 파라미터 및 포맷
3. algorithms        : 핵심 로직 및 수식
4. optional_features : 부가적/선택적 기능
5. error_handling    : 예외 처리 및 엣지 케이스

반드시 아래 JSON 형식으로만 응답:
{{
    "implementations": [],
    "parameters": [],
    "algorithms": [],
    "optional_features": [],
    "error_handling": []
}}
"""

PHASE2_SKIP_KEYWORDS = ["모르", "없어", "없음", "나중에", "패스", "skip", "생략"]

FIELD_LABELS = {
    "problem"        : "기존 문제점",
    "solution"       : "해결 방법",
    "differentiation": "차별성",
    "effect"         : "기대 효과",
}

# ─────────────────────────────────────────────
# 에이전트 클래스
# ─────────────────────────────────────────────

class PatentConsultant:
    def __init__(self, user_id: str):
        self.user_id          = user_id
        self.consultation_idx = self._get_next_idx()
        self.phase            = 1
        self.current_asking   = None
        self.client           = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.state = {
            "problem": None, "solution": None, "differentiation": None, "effect": None,
            "algorithm_steps": [],
            "implementations": [], "parameters": [], "algorithms": [], "optional_features": [], "error_handling": [],
            "raw_log": [], "file_path": None, "confirmed": False,
        }

    def _get_next_idx(self) -> int:
        db = SessionLocal()
        try:
            last = db.query(Consulting).filter(Consulting.user_id == self.user_id).order_by(Consulting.consultation_idx.desc()).with_for_update().first()
            return (last.consultation_idx + 1) if last else 1
        finally: db.close()

    def extract_from_file(self, file_path: str):
        self.state["file_path"] = file_path
        ext = os.path.splitext(file_path)[1].lower()
        extracted_text = ""
        print(f"\n시스템: {ext} 파일 정보를 분석합니다...")
        if ext == ".pdf":
            extracted_text = extract_text_from_pdf(file_path)
            image_paths    = extract_images_from_pdf(file_path)
            for img_p in image_paths[:2]:
                vision_result = self._analyze_vision(img_p)
                self._log_and_extract(f"[도면 분석]:\n{vision_result}", source="file_vision")
        elif ext == ".docx": extracted_text = extract_text_from_docx(file_path)
        elif ext == ".hwp":  extracted_text = extract_text_from_hwp(file_path)
        if extracted_text.strip():
            self._log_and_extract(f"[파일 본문]:\n{extracted_text[:4000]}", source="file_text")

    def _analyze_vision(self, image_path: str) -> str:
        base64_img = encode_image_to_base64(image_path)
        resp = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": [
                {"type": "text",      "text": "이 도면에서 기술적 특징과 작동 단계를 설명해줘."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
            ]}],
            max_tokens=1000,
        )
        return resp.choices[0].message.content

    def _log_and_extract(self, text: str, source: str = "user"):
        self.state["raw_log"].append({"role": source, "content": text[:500]})
        field = self.current_asking
        before = self.state.get(field) if field else None
        self._extract_phase1(text)
        
        # ✅ 폴백: GPT 추출 실패 시 원문 강제 저장
        if field and field in self.state:
            after = self.state.get(field)
            if before is None and after is None:
                self.state[field] = text.strip()
                print(f"  (시스템: '{FIELD_LABELS.get(field, field)}' 항목을 원문으로 보관했습니다.)")

    def _extract_phase1(self, user_input: str):
        prompt = PHASE1_EXTRACT_PROMPT.format(
            problem=self.state["problem"] or "미파악",
            solution=self.state["solution"] or "미파악",
            differentiation=self.state["differentiation"] or "미파악",
            effect=self.state["effect"] or "미파악",
            current_asking=self.current_asking or "없음",
            user_input=user_input
        )
        resp = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": PHASE1_SYSTEM}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        res = json.loads(resp.choices[0].message.content)
        for key in ["problem", "solution", "differentiation", "effect"]:
            if res.get(key): self.state[key] = res[key]

    def collect_algorithm_steps(self):
        print("\n[변리사]: 알고리즘 작동 순서를 단계별로 입력해 주세요. (완료 시 빈 칸으로 엔터)\n")
        steps = []
        while len(steps) < 10:
            step_in = input(f"  {len(steps)+1}단계: ").strip()
            if not step_in:
                if len(steps) >= 3: break
                else: print(f"  ※ 최소 3단계 이상 입력해 주세요. (현재 {len(steps)}단계)"); continue
            steps.append(step_in)
        self.state["algorithm_steps"] = steps
        self.state["raw_log"].append({"role": "user", "content": f"[알고리즘 직접 입력] {steps}"})

    def get_phase1_action(self) -> str | None:
        if not self.state["problem"]: self.current_asking = "problem"; return "기존 기술이나 일상에서 어떤 불편함(문제점)을 느끼셨나요?"
        if not self.state["solution"]: self.current_asking = "solution"; return "그 문제를 극복하기 위해 어떤 아이디어를 사용하셨나요?"
        if not self.state["differentiation"]: self.current_asking = "differentiation"; return "기존 기술들과 비교했을 때 이 발명만의 차별점은 무엇인가요?"
        if not self.state["effect"]: self.current_asking = "effect"; return "이 발명을 통해 얻을 수 있는 기대 효과는 무엇인가요?"
        if len(self.state["algorithm_steps"]) < 3: self.current_asking = None; return "COLLECT_ALGORITHM"
        return None

    def build_summary(self) -> str:
        s = self.state
        def fmt_list(lst): return "\n".join(f"    • {item}" for item in lst) if lst else "    (없음)"
        steps_str = "\n".join(f"  {i+1}단계: {step}" for i, step in enumerate(s["algorithm_steps"]))
        return f"""
━━━━━━━ 📝 발명 상담 최종 요약 ━━━━━━━
【 1부 | 독립항 】
- 문제: {s['problem']}
- 해결: {s['solution']}
- 차별: {s['differentiation']}
- 효과: {s['effect']}
- 단계:
{steps_str}

【 2부 | 종속항 】
🔧 구현수단: {fmt_list(s['implementations'])}
📊 데이터: {fmt_list(s['parameters'])}
⚙️ 핵심로직: {fmt_list(s['algorithms'])}
➕ 부가기능: {fmt_list(s['optional_features'])}
🛡️ 예외처리: {fmt_list(s['error_handling'])}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위 내용이 정확합니까? '네'라고 하시면 최종 정제 후 저장됩니다.
"""

    def confirm_and_save(self) -> str:
        # 최종 정제
        print("\n시스템: 내용을 정문화하고 있습니다...")
        for field, label in FIELD_LABELS.items():
            raw = self.state.get(field)
            if raw:
                resp = self.client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": POLISH_PROMPT.format(field_name=label, raw_text=raw)}], max_tokens=300)
                self.state[field] = resp.choices[0].message.content.strip()

        db = SessionLocal()
        try:
            db.add(Consulting(user_id=self.user_id, consultation_idx=self.consultation_idx, raw_chat_log=self.state["raw_log"], uploaded_file_path=self.state["file_path"], summary_problem=self.state["problem"], summary_solution=self.state["solution"], summary_difference=self.state["differentiation"], summary_effect=self.state["effect"]))
            for i, txt in enumerate(self.state["algorithm_steps"]):
                db.add(AlgorithmStep(user_id=self.user_id, consultation_idx=self.consultation_idx, step_seq=i+1, step_content=txt))
            type_map = {"implementations": "implementation", "parameters": "parameter", "algorithms": "algorithm", "optional_features": "optional", "error_handling": "error_handling"}
            for key, e_type in type_map.items():
                for seq, content in enumerate(self.state[key], start=1):
                    db.add(DetailElement(user_id=self.user_id, consultation_idx=self.consultation_idx, element_type=e_type, seq=seq, content=content))
            db.commit()
            self.state["confirmed"] = True
            if os.path.exists("temp_imgs"): shutil.rmtree("temp_imgs")
            return f"✅ 정제 및 저장 완료 (회차: {self.consultation_idx})"
        except Exception as e:
            db.rollback(); return f"❌ 오류: {str(e)}"
        finally: db.close()

if __name__ == "__main__":
    print("🎓 전문 변리사 상담 에이전트 v3.3")
    u_id = input("사용자 ID: ").strip()
    agent = PatentConsultant(u_id)
    while agent.phase == 1:
        action = agent.get_phase1_action()
        if action is None:
            print("\n[변리사]: 1부 핵심 정보 수집이 완료되었습니다! ✅")
            agent.phase = 2
            break
        if action == "COLLECT_ALGORITHM": agent.collect_algorithm_steps(); continue
        print(f"\n[변리사]: {action}")
        user_in = input("\n[발명가]: ").strip()
        if user_in == "종료": exit()
        if os.path.exists(user_in): agent.extract_from_file(user_in)
        else: agent._log_and_extract(user_in)

    if agent.phase == 2:
        print(f"\n[변리사]: {PHASE2_QUESTION}")
        user_in = input("\n[발명가]: ").strip()
        if not any(kw in user_in.lower() for kw in PHASE2_SKIP_KEYWORDS):
            agent.state["raw_log"].append({"role": "user", "content": user_in[:500]})
            resp = agent.client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": PHASE1_SYSTEM}, {"role": "user", "content": PHASE2_EXTRACT_PROMPT.format(solution=agent.state["solution"] or "", algorithm_steps=agent.state["algorithm_steps"] or [], user_input=user_in)}], response_format={"type": "json_object"})
            res = json.loads(resp.choices[0].message.content)
            for key in ["implementations", "parameters", "algorithms", "optional_features", "error_handling"]:
                if res.get(key): agent.state[key] = res[key]
        print(f"\n[변리사]: {agent.build_summary()}")
        if input("\n[발명가]: ").strip() == "네": print(f"\n시스템: {agent.confirm_and_save()}")
