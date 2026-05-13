import os
import json
import shutil
from pathlib import Path
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

_ENV_DIR = Path(__file__).resolve().parent
load_dotenv(_ENV_DIR.parents[1] / ".env")
load_dotenv(_ENV_DIR / ".env", override=True)

# ─────────────────────────────────────────────
# 모델 설정 (.env의 OPENAI_MODEL로 일괄 변경 가능)
# ─────────────────────────────────────────────
_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
EXTRACT_MODEL  = _DEFAULT_MODEL
CHAT_MODEL     = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
POLISH_MODEL   = _DEFAULT_MODEL

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

# [STEP 1] 추출 및 요약 전용 프롬프트 (gpt-4o용)
PHASE1_EXTRACT_PROMPT = """
당신은 베테랑 변리사입니다. 사용자의 답변에서 발명의 4대 핵심 요소를 정밀 추출하고 특허 명세서 작성 기준의 품질을 평가하세요.

[현재 상태]
- 문제점: {problem}
- 해결방법: {solution}
- 차별성: {differentiation}
- 기대효과: {effect}

[지침]
1. 사용자 답변에서 새로 파악된 내용을 업데이트하세요.
2. 각 항목이 특허 명세서 작성에 충분히 구체적인지 평가(is_sufficient)하고 피드백(feedback)을 작성하세요.
  - 문제점: 단순 불편함이 아닌, 기존 기술의 구조적/기술적 한계가 명시되었는가?
  - 해결방법: 추상적 아이디어가 아닌, 구체적인 기술 구성 요소나 로직이 있는가?
  - 차별성: 종래 기술 대비 추가된 구체적 구성/단계가 명확한가?
3. 반드시 아래 JSON 형식으로만 응답하세요.

{{
    "problem": {{"content": "요약된 문자열 또는 null", "is_sufficient": false, "feedback": "부족한 점 또는 빈 문자열"}},
    "solution": {{"content": "요약된 문자열 또는 null", "is_sufficient": false, "feedback": "부족한 점 또는 빈 문자열"}},
    "differentiation": {{"content": "요약된 문자열 또는 null", "is_sufficient": false, "feedback": "부족한 점 또는 빈 문자열"}},
    "effect": {{"content": "요약된 문자열 또는 null", "is_sufficient": false, "feedback": "부족한 점 또는 빈 문자열"}}
}}
"""

# [STEP 1.5] 포괄적 자동 추출 프롬프트 (파일 업로드 전용)
COMPREHENSIVE_EXTRACT_PROMPT = """
당신은 베테랑 변리사입니다. 사용자가 제출한 문서를 분석하여 특허 출원에 필요한 정보를 추출하고 품질을 평가하세요.

[지침]
1. 문서에 명시된 내용만 추출하고 절대 추측하지 마세요.
2. 4대 요소는 특허 요건에 맞게 구체적인지 평가(is_sufficient)하고 피드백(feedback)을 작성하세요.
  - 문제점: 단순 불편함이 아닌, 기존 기술의 구조적/기술적 한계 유무
  - 해결방법: 추상적 아이디어가 아닌, 구체적인 기술 구성 요소 유무
  - 차별성: 종래 대비 추가된 구체적 구성 명확성
3. 알고리즘 작동 단계(최소 3단계)와 심화 정보도 추출하세요.
4. 반드시 아래 JSON 형식으로만 응답하세요:

{{
    "problem": {{"content": "...", "is_sufficient": false, "feedback": "..."}},
    "solution": {{"content": "...", "is_sufficient": false, "feedback": "..."}},
    "differentiation": {{"content": "...", "is_sufficient": false, "feedback": "..."}},
    "effect": {{"content": "...", "is_sufficient": false, "feedback": "..."}},
    "algorithm_steps": ["1단계", "2단계", "..."],
    "implementations": [], "parameters": [], "algorithms": [], "optional_features": [], "error_handling": []
}}
"""

# [STEP 2] 대화 및 질문 생성 프롬프트 (gpt-4o-mini용)
PHASE1_CHAT_PROMPT = """
당신은 친절하고 전문적인 변리사입니다. 
사용자의 최근 답변에 대해 공감하고, 다음 항목에 대해 질문하세요.

[수집 현황]
{state_summary}

[다음에 물어볼 항목]
- 항목: {target_label}
- 피드백(부족한 점): {target_feedback}

[지침]
1. 사용자의 답변에 대해 전문적인 공감과 짧은 피드백을 먼저 하세요.
2. 만약 '피드백(부족한 점)'이 있다면, 특허 요건을 충족하기 위해 왜 그 정보가 구체적으로 필요한지 설명하며 보완을 요청하세요.
3. 특히 '기대 효과' 질문 시에는 사용자가 얻을 구체적 편익을 상황 중심으로 물어보세요.
"""

POLISH_PROMPT = """
당신은 전문 변리사입니다. 사용자가 설명한 내용을 특허 명세서용 전문 용어로 최종 정제해 주세요.
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
당신은 특허 전문 변리사입니다. 발명가의 답변에서 심화 정보를 추출하세요.

[발명 맥락]
- 해결방법: {solution}
- 작동단계: {algorithm_steps}

사용자 입력: {user_input}

[추출 규칙]
- 사용자의 입력에서 각 항목에 해당하는 내용을 리스트로 추출하세요.
- 언급되지 않은 항목은 빈 리스트 []로 두세요.
- 절대로 추측하지 마세요. 언급된 내용만 추출하세요.

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "implementations": ["구현 수단 (예: YOLO v8, Python, FastAPI 등)"],
  "parameters": ["데이터 파라미터 (예: 사용자 알레르기 정보, 유통기한 등)"],
  "algorithms": ["핵심 로직/수식 (예: 코사인 유사도, 가중치 함수 등)"],
  "optional_features": ["부가적/선택적 기능 (예: 자동 주문 연동 등)"],
  "error_handling": ["예외 처리 (예: 인식 실패 시 수동 입력 UI 등)"]
}}
"""

PHASE2_SKIP_KEYWORDS = ["모르", "없어", "없음", "나중에", "패스", "skip", "생략"]
ALGO_EXIT_KEYWORDS   = ["완료", "끝", "종료", "save", "done", "complete"]

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
        self.client           = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.state = {
            "problem": None, "problem_sufficient": False, "problem_feedback": "",
            "solution": None, "solution_sufficient": False, "solution_feedback": "",
            "differentiation": None, "differentiation_sufficient": False, "differentiation_feedback": "",
            "effect": None, "effect_sufficient": False, "effect_feedback": "",
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
        if ext == ".pdf":
            extracted_text = extract_text_from_pdf(file_path)
            image_paths    = extract_images_from_pdf(file_path)
            for img_p in image_paths[:2]:
                vision_result = self._analyze_vision(img_p)
                self.state["raw_log"].append({"role": "file_vision", "content": vision_result[:500]})
        elif ext == ".docx": extracted_text = extract_text_from_docx(file_path)
        elif ext == ".hwp":  extracted_text = extract_text_from_hwp(file_path)
        if extracted_text.strip():
            self.state["raw_log"].append({"role": "file_text", "content": extracted_text[:4000]})
            self._analyze_comprehensive(extracted_text[:4000])

    def _analyze_comprehensive(self, text: str):
        """문서 전체를 분석하여 모든 가능한 필드를 한꺼번에 채움"""
        resp = self.client.chat.completions.create(
            model=EXTRACT_MODEL,
            messages=[
                {"role": "system", "content": PHASE1_SYSTEM},
                {"role": "user", "content": f"{COMPREHENSIVE_EXTRACT_PROMPT}\n\n[문서 내용]\n{text}"}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        
        for key in ["problem", "solution", "differentiation", "effect"]:
            val = data.get(key)
            if val and val.get("content"):
                self.state[key] = val["content"]
                self.state[f"{key}_sufficient"] = val.get("is_sufficient", False)
                self.state[f"{key}_feedback"] = val.get("feedback", "")
        
        if data.get("algorithm_steps"):
            self.state["algorithm_steps"] = data["algorithm_steps"]
            
        for key in ["implementations", "parameters", "algorithms", "optional_features", "error_handling"]:
            if data.get(key):
                if not self.state[key]: self.state[key] = []
                self.state[key].extend(data[key])

    def _analyze_vision(self, image_path: str) -> str:
        base64_img = encode_image_to_base64(image_path)
        resp = self.client.chat.completions.create(
            model=EXTRACT_MODEL,
            messages=[{"role": "user", "content": [
                {"type": "text",      "text": "이 도면에서 기술적 특징과 작동 단계를 설명해줘."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
            ]}],
            max_completion_tokens=1000,
        )
        return resp.choices[0].message.content

    def collect_algorithm_steps(self):
        print("\n[변리사]: 알고리즘 작동 순서를 단계별로 입력해 주세요. (최대 10단계, '완료' 입력 시 종료)\n")
        steps = []
        while len(steps) < 10:
            step_in = input(f"  {len(steps)+1}단계: ").strip()
            if not step_in or step_in in ALGO_EXIT_KEYWORDS:
                if len(steps) >= 3: break
                else: print(f"  ※ 최소 3단계 이상 입력해 주세요. (현재 {len(steps)}단계)"); continue
            steps.append(step_in)
        self.state["algorithm_steps"] = steps
        self.state["raw_log"].append({"role": "user", "content": f"[알고리즘 직접 입력] {steps}"})

    def _extract_and_interact(self, user_input: str) -> str:
        """
        [하이브리드 전략 적용]
        1. gpt-4o: 고성능 추출 및 요약
        2. gpt-4o-mini: 저렴하고 자연스러운 질문 생성
        """
        all_filled = all(self.state.get(f"{k}_sufficient", False) for k in ["problem", "solution", "differentiation", "effect"])
        if all_filled and len(self.state["algorithm_steps"]) >= 3: return None
        if all_filled and len(self.state["algorithm_steps"]) < 3 and user_input.startswith("["): return "COLLECT_ALGORITHM"

        target_field = None
        for key in ["problem", "solution", "differentiation", "effect"]:
            if not self.state.get(f"{key}_sufficient", False):
                target_field = key
                break

        # STEP 1: gpt-4o 추출
        extract_prompt = PHASE1_EXTRACT_PROMPT.format(
            problem=self.state["problem"] or "미파악",
            solution=self.state["solution"] or "미파악",
            differentiation=self.state["differentiation"] or "미파악",
            effect=self.state["effect"] or "미파악"
        )
        ext_resp = self.client.chat.completions.create(
            model=EXTRACT_MODEL,
            messages=[{"role": "system", "content": PHASE1_SYSTEM}, {"role": "user", "content": f"{extract_prompt}\n\n사용자 입력: {user_input}"}],
            response_format={"type": "json_object"}
        )
        ext_data = json.loads(ext_resp.choices[0].message.content)
        for key in ["problem", "solution", "differentiation", "effect"]:
            val = ext_data.get(key)
            if val and val.get("content"):
                self.state[key] = val["content"]
                self.state[f"{key}_sufficient"] = val.get("is_sufficient", False)
                self.state[f"{key}_feedback"] = val.get("feedback", "")
        
        if target_field and not self.state.get(f"{target_field}_sufficient", False):
            if user_input and not user_input.startswith("[") and user_input != "상담을 시작합니다." and not self.state[target_field]:
                self.state[target_field] = user_input.strip()

        all_filled_now = all(self.state.get(f"{k}_sufficient", False) for k in ["problem", "solution", "differentiation", "effect"])
        if all_filled_now and len(self.state["algorithm_steps"]) < 3: return "COLLECT_ALGORITHM"
        if all_filled_now and len(self.state["algorithm_steps"]) >= 3: return None

        # STEP 2: gpt-4o-mini 질문
        history = []
        for m in self.state["raw_log"][-6:]:
            role = m["role"] if m["role"] in ("user", "assistant") else "user"
            history.append({"role": role, "content": m["content"]})
        state_summary = "\n".join([f"- {FIELD_LABELS[k]}: {self.state[k] or '미파악'}" for k in ["problem", "solution", "differentiation", "effect"]])
        target_label = FIELD_LABELS.get(target_field, "전반적인 내용")
        target_feedback = self.state.get(f"{target_field}_feedback", "")
        
        chat_resp = self.client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": PHASE1_CHAT_PROMPT.format(state_summary=state_summary, target_label=target_label, target_feedback=target_feedback)},
                *history,
                {"role": "user", "content": f"사용자의 최근 발언: {user_input}\n\n위 발언에 공감하고, 다음 항목({target_label})에 대해 질문해줘."}
            ]
        )
        return chat_resp.choices[0].message.content.strip()

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
        for field, label in FIELD_LABELS.items():
            raw = self.state.get(field)
            if raw:
                resp = self.client.chat.completions.create(model=POLISH_MODEL, messages=[{"role": "user", "content": POLISH_PROMPT.format(field_name=label, raw_text=raw)}], max_completion_tokens=300)
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
            db.commit(); self.state["confirmed"] = True
            return f"✅ 정제 및 저장 완료 (회차: {self.consultation_idx})"
        except Exception as e:
            db.rollback(); return f"❌ 오류: {str(e)}"
        finally: db.close()

if __name__ == "__main__":
    print("🎓 전문 변리사 상담 에이전트 v3.5")
    u_id = input("사용자 ID: ").strip()
    agent = PatentConsultant(u_id)
    action = agent._extract_and_interact("상담을 시작합니다.") 
    while agent.phase == 1:
        if action is None:
            print("\n[변리사]: 1부 핵심 정보 수집이 완료되었습니다! ✅")
            agent.phase = 2
            break
        if action == "COLLECT_ALGORITHM": 
            agent.collect_algorithm_steps()
            all_filled = all(agent.state.get(f"{k}_sufficient", False) for k in ["problem", "solution", "differentiation", "effect"])
            action = None if (all_filled and len(agent.state["algorithm_steps"]) >= 3) else agent._extract_and_interact("[알고리즘 수집 완료]")
            continue
        print(f"\n[변리사]: {action}")
        user_in = input("\n[발명가]: ").strip()
        if user_in == "종료": exit()
        if os.path.exists(user_in):
            agent.extract_from_file(user_in)
            all_filled = all(agent.state.get(f"{k}_sufficient", False) for k in ["problem", "solution", "differentiation", "effect"])
            if all_filled and len(agent.state["algorithm_steps"]) >= 3:
                action = None
            elif all_filled:
                action = "COLLECT_ALGORITHM"
            else:
                action = agent._extract_and_interact("[파일 분석 완료. 부족한 항목 확인 후 질문하세요.]")
        else:
            agent.state["raw_log"].append({"role": "user", "content": user_in})
            action = agent._extract_and_interact(user_in)

    if agent.phase == 2:
        print(f"\n[변리사]: {PHASE2_QUESTION}")
        user_in = input("\n[발명가]: ").strip()
        if not any(kw in user_in.lower() for kw in PHASE2_SKIP_KEYWORDS):
            agent.state["raw_log"].append({"role": "user", "content": user_in[:500]})
            # 수정: algorithm_steps 맥락 복원
            resp = agent.client.chat.completions.create(model="gpt-4o", messages=[{"role": "system", "content": PHASE1_SYSTEM}, {"role": "user", "content": PHASE2_EXTRACT_PROMPT.format(solution=agent.state["solution"] or "", algorithm_steps=agent.state["algorithm_steps"] or [], user_input=user_in)}], response_format={"type": "json_object"})
            res = json.loads(resp.choices[0].message.content)
            for key in ["implementations", "parameters", "algorithms", "optional_features", "error_handling"]:
                extracted = res.get(key, [])
                validated = [item for item in extracted if item and item.strip()]
                if validated: agent.state[key].extend(validated)
        print(f"\n[변리사]: {agent.build_summary()}")
        if input("\n[발명가]: ").strip() == "네": print(f"\n시스템: {agent.confirm_and_save()}")
