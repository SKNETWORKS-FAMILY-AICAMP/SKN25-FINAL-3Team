import streamlit as st
import os
import sys
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
CONSULTATION_AGENT_DIR = REPO_ROOT / "agents" / "consultation"
sys.path.insert(0, str(CONSULTATION_AGENT_DIR))
load_dotenv(REPO_ROOT / ".env")
load_dotenv(CONSULTATION_AGENT_DIR / ".env", override=True)

from consultation_agent import PatentConsultant, FIELD_LABELS, PHASE2_QUESTION, PHASE2_SKIP_KEYWORDS, PHASE2_EXTRACT_PROMPT, PHASE1_SYSTEM
from document_utils import extract_text_from_pdf, extract_text_from_docx, extract_text_from_hwp, extract_images_from_pdf

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Patent AI Expert",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CSS 스타일링 (Premium Design)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #f8f9fa;
    }

    /* 채팅 메시지 스타일 */
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        color: white;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #fbbf24;
    }

    /* 상태 카드 스타일 */
    .status-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #fbbf24;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    
    .status-label {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-value {
        font-size: 0.95rem;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.user_id = "User_Streamlit"
    st.session_state.agent = PatentConsultant(st.session_state.user_id)
    # 초기 인사말
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! 전문 변리사 AI 에이전트입니다. 귀하의 소중한 아이디어를 특허로 만들기 위해 상담을 시작하겠습니다."})
    # 첫 질문 유도
    action = st.session_state.agent.get_phase1_action()
    st.session_state.messages.append({"role": "assistant", "content": action})

if "algorithm_collecting" not in st.session_state:
    st.session_state.algorithm_collecting = False
    st.session_state.temp_steps = []

# ─────────────────────────────────────────────
# 사이드바: 현재 추출 정보 현황
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🎓 Patent Status")
    st.markdown("현재까지 파악된 발명의 핵심 요소입니다.")
    
    agent_state = st.session_state.agent.state
    
    for key, label in FIELD_LABELS.items():
        val = agent_state.get(key)
        st.markdown(f"""
        <div class="status-card">
            <div class="status-label">{label}</div>
            <div class="status-value">{val if val else '미파악'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### ⚙️ Algorithm Steps")
    steps = agent_state.get("algorithm_steps", [])
    if steps:
        for i, s in enumerate(steps):
            st.caption(f"{i+1}. {s}")
    else:
        st.caption("알고리즘 순서가 아직 수집되지 않았습니다.")

# ─────────────────────────────────────────────
# 메인 채팅 UI
# ─────────────────────────────────────────────
st.title("🎓 AI Patent Consultant")
st.markdown("---")

# 채팅 메시지 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ─────────────────────────────────────────────
# 하단 레이아웃 (채팅 입력 + 플러스 버튼)
# ─────────────────────────────────────────────
input_col, plus_col = st.columns([10, 1])

with plus_col:
    # 팝오버를 사용해 '+' 버튼 구현
    with st.popover("➕", help="파일 업로드"):
        st.markdown("### 📄 파일 업로드")
        uploaded_file = st.file_uploader("명세서 파일 (PDF, DOCX, HWP)", type=['pdf', 'docx', 'hwp'], label_visibility="collapsed")
        if uploaded_file:
            temp_dir = "temp_uploads"
            if not os.path.exists(temp_dir): os.makedirs(temp_dir)
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            
            st.session_state.messages.append({"role": "user", "content": f"📄 파일 업로드됨: `{uploaded_file.name}`"})
            with st.spinner("파일 분석 중..."):
                st.session_state.agent.extract_from_file(file_path)
                action = st.session_state.agent.get_phase1_action()
                if action:
                    if action == "COLLECT_ALGORITHM":
                        st.session_state.algorithm_collecting = True
                        msg = "핵심 정보 파악이 완료되었습니다. 이제 알고리즘 작동 순서를 단계별로 말씀해 주세요. (최소 3단계, 완료 시 '완료' 입력)"
                    else:
                        msg = f"파일 분석 완료! 계속해서 상담을 진행합니다.\n\n**[질문]**: {action}"
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            st.rerun()

with input_col:
    prompt = st.chat_input("변리사에게 메시지를 입력하세요...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    agent = st.session_state.agent
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # 알고리즘 수집 모드
        if st.session_state.algorithm_collecting:
            if prompt in ["완료", "끝", "done"]:
                if len(st.session_state.temp_steps) >= 3:
                    agent.state["algorithm_steps"] = st.session_state.temp_steps
                    st.session_state.algorithm_collecting = False
                    msg = "알고리즘 수집 완료! ✅"
                    response_placeholder.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    
                    action = agent.get_phase1_action()
                    if action is None:
                        agent.phase = 2
                        msg2 = f"1부 핵심 정보 수집이 완료되었습니다! ✅\n\n{PHASE2_QUESTION}"
                        st.markdown(msg2)
                        st.session_state.messages.append({"role": "assistant", "content": msg2})
                    else:
                        st.markdown(action)
                        st.session_state.messages.append({"role": "assistant", "content": action})
                else:
                    msg = f"최소 3단계 이상 입력해 주세요. (현재 {len(st.session_state.temp_steps)}단계)"
                    response_placeholder.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                st.session_state.temp_steps.append(prompt)
                msg = f"{len(st.session_state.temp_steps)}단계 등록됨. 다음 단계를 입력하거나 '완료'를 입력하세요."
                response_placeholder.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
        
        # 페이즈 2: 심화 정보 및 최종 요약
        elif agent.phase == 2 and not agent.state["confirmed"]:
            if prompt == "네":
                with st.spinner("최종 정제 및 저장 중..."):
                    result = agent.confirm_and_save()
                    response_placeholder.markdown(result)
                    st.session_state.messages.append({"role": "assistant", "content": result})
            else:
                if not any(kw in prompt.lower() for kw in PHASE2_SKIP_KEYWORDS):
                    agent.state["raw_log"].append({"role": "user", "content": prompt[:500]})
                    resp = agent.client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[
                            {"role": "system", "content": PHASE1_SYSTEM}, 
                            {"role": "user", "content": PHASE2_EXTRACT_PROMPT.format(
                                solution=agent.state["solution"] or "", 
                                algorithm_steps=agent.state["algorithm_steps"] or [], 
                                user_input=prompt
                            )}
                        ], 
                        response_format={"type": "json_object"}
                    )
                    res = json.loads(resp.choices[0].message.content)
                    for key in ["implementations", "parameters", "algorithms", "optional_features", "error_handling"]:
                        if res.get(key): agent.state[key] = res[key]
                
                summary = agent.build_summary()
                response_placeholder.markdown(summary)
                st.session_state.messages.append({"role": "assistant", "content": summary})

        # 페이즈 1: 기본 상담
        else:
            agent._log_and_extract(prompt)
            action = agent.get_phase1_action()
            
            if action == "COLLECT_ALGORITHM":
                st.session_state.algorithm_collecting = True
                msg = "핵심 정보 파악이 완료되었습니다. 이제 알고리즘 작동 순서를 단계별로 말씀해 주세요. (최소 3단계, 완료 시 '완료' 입력)"
                response_placeholder.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            elif action is None:
                agent.phase = 2
                msg = f"1부 핵심 정보 수집이 완료되었습니다! ✅\n\n{PHASE2_QUESTION}"
                response_placeholder.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                response_placeholder.markdown(action)
                st.session_state.messages.append({"role": "assistant", "content": action})
    
    st.rerun()
