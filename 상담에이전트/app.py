import streamlit as st
import os
import json
import time
from consultation_agent import PatentConsultant, PHASE2_QUESTION, PHASE2_EXTRACT_PROMPT, PHASE1_SYSTEM, ALGO_EXIT_KEYWORDS

# ─────────────────────────────────────────────
# 1. 페이지 설정 및 프리미엄 디자인 (CSS)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Patent AI | 전문 변리사 상담 에이전트",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* 채팅 메시지 스타일링 */
    .stChatMessage {
        border-radius: 20px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(5px);
    }
    
    [data-testid="chatAvatarIcon-user"] {
        background-color: #4A90E2 !important;
    }
    
    [data-testid="chatAvatarIcon-assistant"] {
        background-color: #2C3E50 !important;
    }
    
    /* 카드형 메트릭/정보 박스 */
    .info-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #4A90E2;
    }
    
    .info-card h4 {
        margin: 0;
        color: #1E293B;
        font-size: 0.9rem;
        font-weight: 700;
    }
    
    .info-card p {
        margin: 0.5rem 0 0 0;
        color: #64748B;
        font-size: 0.85rem;
        line-height: 1.4;
    }

    /* 버튼 스타일 */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* 타이틀 애니메이션 */
    .main-title {
        background: linear-gradient(90deg, #1E293B, #4A90E2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. 세션 상태 관리
# ─────────────────────────────────────────────
if "agent" not in st.session_state: st.session_state.agent = None
if "messages" not in st.session_state: st.session_state.messages = []
if "user_id" not in st.session_state: st.session_state.user_id = ""
if "phase" not in st.session_state: st.session_state.phase = 1
if "collecting_steps" not in st.session_state: st.session_state.collecting_steps = False

def initialize_agent(u_id):
    st.session_state.user_id = u_id
    st.session_state.agent = PatentConsultant(u_id)
    st.session_state.phase = 1
    st.session_state.collecting_steps = False
    st.session_state.messages = []
    
    with st.spinner("전문 변리사 에이전트를 연결하고 있습니다..."):
        greeting = st.session_state.agent._extract_and_interact("상담을 시작합니다.")
        st.session_state.messages.append({"role": "assistant", "content": greeting})

# ─────────────────────────────────────────────
# 3. 사이드바 (실시간 분석 보드)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #1E293B;'>🎓 Patent AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.9rem;'>전문 특허 상담 시스템 v3.5</p>", unsafe_allow_html=True)
    
    input_uid = st.text_input("사용자 ID", value=st.session_state.user_id, placeholder="아이디를 입력하세요")
    
    if input_uid and input_uid != st.session_state.user_id:
        initialize_agent(input_uid)
        st.rerun()

    st.divider()

    if st.session_state.agent:
        st.subheader("🔍 실시간 추출 정보")
        s = st.session_state.agent.state
        
        # Phase 1: 핵심 4대 요소
        for key, label, icon in [
            ("problem", "🚩 문제점", "🔴"), 
            ("solution", "💡 해결방법", "🔵"), 
            ("differentiation", "✨ 차별성", "🟢"), 
            ("effect", "🚀 기대효과", "🟣")
        ]:
            if s[key]:
                with st.expander(f"{label}", expanded=False):
                    st.write(s[key])
            else:
                st.caption(f"{icon} {label.split(' ')[1]}: 탐색 중...")

        # 알고리즘 단계
        if s["algorithm_steps"]:
            with st.expander(f"⚙️ 작동 알고리즘 ({len(s['algorithm_steps'])}단계)", expanded=True):
                for idx, step in enumerate(s["algorithm_steps"]):
                    st.markdown(f"**{idx+1}.** {step}")

        # 심화 정보 (Phase 2)
        if st.session_state.phase >= 2:
            st.divider()
            st.subheader("🛠 심화 정보")
            detail_keys = {
                "implementations": "🔧 구현수단",
                "parameters": "📊 데이터",
                "algorithms": "⚙️ 핵심로직",
                "optional_features": "➕ 부가기능",
                "error_handling": "🛡️ 예외처리"
            }
            for key, label in detail_keys.items():
                if s[key]:
                    with st.expander(label, expanded=False):
                        for item in s[key]:
                            st.write(f"- {item}")

        st.divider()
        # 파일 업로드
        st.markdown("### 📎 관련 문서 분석")
        uploaded_file = st.file_uploader("PDF, DOCX, HWP", type=["pdf", "docx", "hwp"], label_visibility="collapsed")
        if uploaded_file:
            file_key = f"up_{uploaded_file.name}_{uploaded_file.size}"
            if file_key not in st.session_state:
                with st.spinner("문서를 읽고 분석하는 중..."):
                    temp_dir = "temp_uploads"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    st.session_state.agent.extract_from_file(temp_path)
                    res = st.session_state.agent._extract_and_interact("[파일 분석 완료]")
                    
                    st.session_state.messages.append({"role": "user", "content": f"📎 파일을 업로드했습니다: `{uploaded_file.name}`"})
                    if res:
                        st.session_state.messages.append({"role": "assistant", "content": res})
                    st.session_state[file_key] = True
                    st.rerun()

    if st.button("🔄 상담 초기화", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()

# ─────────────────────────────────────────────
# 4. 메인 채팅 인터페이스
# ─────────────────────────────────────────────
st.markdown("<h1 class='main-title'>🎓 전문 변리사 AI 상담</h1>", unsafe_allow_html=True)

if not st.session_state.agent:
    st.info("💡 시작하시려면 왼쪽 사이드바에 **사용자 ID**를 입력해 주세요.")
    
    # 소개 섹션
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 이 에이전트가 도와드리는 것
        - **핵심 요소 추출**: 발명의 문제점, 해결방법, 차별성, 효과를 정밀 분석합니다.
        - **알고리즘 구조화**: 작동 단계를 논리적으로 정리합니다.
        - **종속항 심화 분석**: 구현 수단 및 예외 처리까지 꼼꼼히 챙깁니다.
        - **특허 명세서 요약**: 변리사 수준의 전문 용어로 정제합니다.
        """)
    with col2:
        st.image("https://img.icons8.com/illustrations/external-tulpahn-outline-color-tulpahn/100/external-patent-law-and-justice-tulpahn-outline-color-tulpahn.png", width=200)
    st.stop()

# 메시지 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─────────────────────────────────────────────
# 5. 상담 로직 처리
# ─────────────────────────────────────────────
if prompt := st.chat_input("발명에 대해 자유롭게 설명해 주세요..."):
    # 1. 사용자 메시지 기록 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    agent = st.session_state.agent
    
    # 2. 어시스턴트 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("변리사 AI가 분석 중입니다..."):
            response = ""
            
            # Phase 1: 핵심 요소 및 알고리즘 수집
            if st.session_state.phase == 1:
                if st.session_state.collecting_steps:
                    # 알고리즘 수집 모드
                    cleaned_in = prompt.strip().lower()
                    if cleaned_in in ALGO_EXIT_KEYWORDS or not cleaned_in:
                        if len(agent.state["algorithm_steps"]) >= 3:
                            st.session_state.collecting_steps = False
                            response = agent._extract_and_interact("[알고리즘 수집 완료]")
                        else:
                            response = f"⚠️ 특허 구성을 위해 최소 3단계 이상의 설명이 필요합니다.\n현재 **{len(agent.state['algorithm_steps'])}단계**입니다. 다음 단계를 계속 말씀해 주세요."
                    else:
                        agent.state["algorithm_steps"].append(prompt)
                        if len(agent.state["algorithm_steps"]) >= 10:
                            st.session_state.collecting_steps = False
                            response = agent._extract_and_interact("[알고리즘 10단계 수집 완료]")
                        else:
                            response = f"**{len(agent.state['algorithm_steps'])+1}단계**를 말씀해 주세요.\n(마치시려면 '완료' 또는 '끝'이라고 입력해 주세요.)"
                else:
                    # 일반 4대 요소 추출 모드
                    agent.state["raw_log"].append({"role": "user", "content": prompt})
                    response = agent._extract_and_interact(prompt)
                
                # 상태 전환 체크
                if response == "COLLECT_ALGORITHM":
                    st.session_state.collecting_steps = True
                    response = "핵심 요소 파악이 순조롭습니다! 👏 이제 이 발명이 **어떤 순서로 작동하는지(알고리즘)** 단계별로 설명 부탁드립니다.\n\n먼저 **1단계**는 무엇인가요?"
                elif response is None:
                    st.session_state.phase = 2
                    response = f"훌륭합니다! 독립항 구성을 위한 핵심 정보 수집이 완료되었습니다. ✅\n\n{PHASE2_QUESTION}"
            
            # Phase 2: 심화 정보 수집
            elif st.session_state.phase == 2:
                agent.state["raw_log"].append({"role": "user", "content": prompt})
                prompt_p2 = PHASE2_EXTRACT_PROMPT.format(
                    solution=agent.state["solution"] or "", 
                    algorithm_steps=agent.state["algorithm_steps"] or [], 
                    user_input=prompt
                )
                
                # gpt-4o-mini를 통한 심화 정보 추출
                resp = agent.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PHASE1_SYSTEM},
                        {"role": "user", "content": prompt_p2}
                    ],
                    response_format={"type": "json_object"}
                )
                res = json.loads(resp.choices[0].message.content)
                
                found_new = False
                for key in ["implementations", "parameters", "algorithms", "optional_features", "error_handling"]:
                    extracted = res.get(key, [])
                    validated = [item for item in extracted if item and item.strip()]
                    if validated:
                        agent.state[key].extend(validated)
                        found_new = True
                
                if found_new:
                    response = "상세 정보가 잘 기록되었습니다! 📝 추가로 덧붙일 내용이 있으신가요? 없으시면 사이드바의 **'최종 요약 리포트 발행'** 버튼을 눌러주세요."
                else:
                    response = "말씀하신 내용을 검토했습니다. 더 구체적인 기술적 특징이나 예외 상황에 대해 들려주실 말씀이 있을까요?"

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()

# ─────────────────────────────────────────────
# 6. 리포트 발행 및 DB 저장 (사이드바 하단)
# ─────────────────────────────────────────────
if st.session_state.agent and st.session_state.phase >= 2:
    with st.sidebar:
        st.divider()
        st.markdown("### 🏁 상담 마무리")
        
        if st.button("📄 최종 요약 리포트 발행", use_container_width=True, type="primary"):
            with st.spinner("리포트를 생성 중입니다..."):
                summary = st.session_state.agent.build_summary()
                st.session_state.messages.append({"role": "assistant", "content": summary})
                st.rerun()
                
        if st.button("💾 DB 및 클라우드 저장", use_container_width=True):
            with st.spinner("데이터를 정제하고 보안 서버에 저장 중입니다..."):
                res = st.session_state.agent.confirm_and_save()
                st.success(res)
                st.balloons()
                time.sleep(2)
                st.info("상담이 성공적으로 종료되었습니다. 감사합니다.")
