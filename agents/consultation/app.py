import streamlit as st
import os
import json
import time
from pathlib import Path
import requests  # API 호출용 추가
from dotenv import load_dotenv

_ENV_DIR = Path(__file__).resolve().parent
load_dotenv(_ENV_DIR.parents[1] / ".env")
load_dotenv(_ENV_DIR / ".env", override=True)

import agent_payloads
from consultation_agent import PatentConsultant, PHASE2_QUESTION, PHASE2_EXTRACT_PROMPT, PHASE1_SYSTEM, ALGO_EXIT_KEYWORDS, PHASE2_SKIP_KEYWORDS
from prior_art_agent import run_prior_art_agent
from claim_agent import fetch_consultation_from_db, save_claims_to_db

# 런팟 대시보드의 'Connect' -> 'HTTP Service (Port 8000)'에서 복사한 주소를 넣으세요.
# 맨 뒤에 슬래시(/)는 빼고 입력합니다.
BACKEND_URL = os.getenv("CLAIM_BACKEND_URL", "https://iu0c50cr6tlboh-8000.proxy.runpod.net")
# 백엔드 헬스 체크
def is_backend_available():
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# 청구항 생성 API 호출 함수

def generate_claims(user_id, consultation_idx):
    url = f"{BACKEND_URL}/generate-claims"
    
    if not is_backend_available():
        return {"error": "연결 오류: 백엔드 서버가 실행 중인지 확인하세요."}
    
    try:
        # 1. claim_agent를 통해 DB에서 프롬프트용 텍스트를 꺼내옵니다.
        consultation_note = fetch_consultation_from_db(user_id, consultation_idx)
    except Exception as e:
        return {"error": f"DB 조회 오류: {str(e)}"}
        
    # 2. 런팟(main.py) 스펙에 맞게 payload 구성
    payload = {
        "consultation_note": consultation_note
    }
    
    try:
        response = requests.post(url, json=payload, timeout=180) 
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API 오류: {response.status_code} - {response.json().get('detail')}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"연결 오류: {str(e)}"}


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
if "prior_art_result" not in st.session_state: st.session_state.prior_art_result = None
if "generated_claim" not in st.session_state: st.session_state.generated_claim = ""

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

    backend_ok = is_backend_available()
    if backend_ok:
        st.success(f"백엔드 서버 연결됨: {BACKEND_URL}")
    else:
        st.error(
            "백엔드 서버 미연결: main.py를 실행해 주세요.\n"
            f"URL: {BACKEND_URL}/health"
        )

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
                is_ok = s.get(f"{key}_sufficient", False)
                status_icon = "✅" if is_ok else "⚠️"
                with st.expander(f"{status_icon} {label.split(' ')[1]}", expanded=not is_ok):
                    st.write(s[key])
                    if not is_ok and s.get(f"{key}_feedback"):
                        st.caption(f"💬 {s[f'{key}_feedback']}")
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
                    
                    agent = st.session_state.agent
                    all_filled = all(agent.state.get(f"{k}_sufficient", False) for k in ["problem", "solution", "differentiation", "effect"])
                    if all_filled and len(agent.state["algorithm_steps"]) >= 3:
                        st.session_state.phase = 2
                        res = (
                            "문서에서 핵심 내용을 잘 파악했습니다. "
                            "특허 요건상 기본 구성은 갖춰졌으나, "
                            "청구항을 더 탄탄하게 만들기 위해 몇 가지 확인이 더 필요합니다.\n\n"
                            f"{PHASE2_QUESTION}"
                        )
                    elif all_filled:
                        st.session_state.collecting_steps = True
                        res = "핵심 요소 파악이 순조롭습니다! 👏 문서에 구체적인 작동 순서가 부족하네요. 이 발명이 **어떤 순서로 작동하는지(알고리즘)** 단계별로 설명 부탁드립니다.\n\n먼저 **1단계**는 무엇인가요?"
                    else:
                        res = agent._extract_and_interact("[파일 분석 완료. 부족한 항목 확인 후 질문하세요.]")
                    
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
                            current_len = len(agent.state["algorithm_steps"])
                            response = f"**{current_len}단계**까지 입력되었습니다. **{current_len + 1}단계**를 말씀해 주세요.\n(마치시려면 '완료' 또는 '끝'이라고 입력해 주세요.)"
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
                    response = (
                        "핵심 내용을 잘 파악했습니다. "
                        "특허 요건상 기본 구성은 갖춰졌으나, "
                        "청구항을 더 탄탄하게 만들기 위해 몇 가지 확인이 더 필요합니다.\n\n"
                        f"{PHASE2_QUESTION}"
                    )
            
            # Phase 2: 심화 정보 수집
            elif st.session_state.phase == 2:
                agent.state["raw_log"].append({"role": "user", "content": prompt})

                # 종료 키워드 입력 시 바로 마무리 안내
                if any(kw in prompt.strip() for kw in PHASE2_SKIP_KEYWORDS):
                    response = "알겠습니다! 입력하신 내용으로 상담을 마무리하겠습니다. 👍\n\n사이드바의 **'최종 요약 리포트 발행'** 버튼을 눌러주세요."
                else:
                    prompt_p2 = PHASE2_EXTRACT_PROMPT.format(
                        solution=agent.state["solution"] or "",
                        algorithm_steps=agent.state["algorithm_steps"] or [],
                        user_input=prompt
                    )

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
                        response = "상세 정보가 잘 기록되었습니다! 📝 추가로 덧붙일 내용이 있으신가요?\n없으시면 **'없어'** 또는 **'패스'** 라고 하시거나, 사이드바의 **'최종 요약 리포트 발행'** 버튼을 눌러주세요."
                    else:
                        response = "말씀하신 내용에서 추출할 기술 정보가 없었습니다. 구현 수단, 데이터, 예외 처리 등을 구체적으로 말씀해주시거나, **'없어'** 라고 하시면 마무리할게요."

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
                
                # [모듈화된 Payload 전송 시스템] 
                master_payload = agent_payloads.build_invention_payload(
                    st.session_state.agent.state, 
                    st.session_state.agent.user_id, 
                    st.session_state.agent.consultation_idx
                )
                
                prior_art_payload = agent_payloads.build_prior_art_payload(master_payload)
                claims_payload = agent_payloads.build_claim_payload(master_payload)
                spec_payload = agent_payloads.build_specification_payload(master_payload)
                
                st.success(res)
                st.balloons()

                # 선행기술조사 에이전트 실행
                with st.spinner("🔍 선행기술조사 에이전트가 분석 중입니다... (1~2분 소요)"):
                    prior_art_result = run_prior_art_agent(master_payload)
                    st.session_state.prior_art_result = prior_art_result

        if st.session_state.prior_art_result:
            prior_art_result = st.session_state.prior_art_result
            st.subheader("📋 선행기술조사 결과")

            overall = prior_art_result.get("overall_risk", {})
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(overall.get("level"), "⚪")
            st.markdown(f"**전체 리스크: {risk_color} {overall.get('level', '').upper()}**")
            st.info(overall.get("summary", ""))

            for item in prior_art_result.get("prior_art_results", []):
                risk_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.get("risk_level"), "⚪")
                with st.expander(f"{item['rank']}위 | {risk_icon} {item.get('title', item['file_name'])} (유사도: {item['similarity_score']:.2%})"):
                    st.markdown(f"**출원번호:** {item.get('patent_number', '-')}")
                    st.markdown(f"**리스크:** {item.get('risk_level', '-').upper()}")

                    if item.get("risk_reasons"):
                        st.markdown("**리스크 이유:**")
                        for r in item["risk_reasons"]:
                            st.markdown(f"- {r}")

                    if item.get("evidence_sentences"):
                        st.markdown("**근거 문장:**")
                        for e in item["evidence_sentences"]:
                            st.markdown(f"- 선행특허: *{e.get('patent_text', '')}*")
                            st.markdown(f"  → 본 발명: {e.get('invention_text', '')}")

                    if item.get("differentiating_points"):
                        st.markdown("**본 발명의 차별점:**")
                        for d in item["differentiating_points"]:
                            st.markdown(f"- {d}")

                    if item.get("recommendation"):
                        st.markdown(f"**대응 전략:** {item['recommendation']}")

            st.info("상담이 성공적으로 종료되었으며, 선행기술조사까지 완료되었습니다.")

            # 청구항 생성 섹션 추가 (버튼은 사이드바에 유지, 결과는 메인 화면으로 전송)
            st.divider()
            st.subheader("📝 특허 청구항 생성")
            
            is_saved_to_db = st.session_state.agent.state.get("confirmed", False)

            if not is_saved_to_db:
                st.warning("⚠️ 청구항을 생성하려면 먼저 위의 '💾 DB 및 클라우드 저장' 버튼을 눌러주세요.")
            else:
                if st.button("🤖 AI 모델로 청구항 생성", use_container_width=True, type="primary"):
                    with st.spinner("백엔드가 DB를 조회하여 청구항을 생성 중입니다..."):
                        
                        u_id = st.session_state.agent.user_id
                        c_idx = st.session_state.agent.consultation_idx
                        
                        # API 호출
                        generated = generate_claims(u_id, c_idx)
                        st.session_state.generated_claim = generated
                        
                        if "error" not in generated:
                            # ▼▼▼ [DB 저장 로직 추가] ▼▼▼
                            try:
                                save_claims_to_db(
                                    user_id=u_id, 
                                    consultation_idx=c_idx, 
                                    claim_1=generated.get('claim_1', ''), 
                                    dependent_claims=generated.get('dependent_claims', '')
                                )
                            except Exception as e:
                                st.error(f"DB 저장 중 오류가 발생했습니다: {e}")
                            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                            # 기존 렌더링 메시지 지우기
                            st.session_state.messages = [
                                msg for msg in st.session_state.messages 
                                if not (msg["role"] == "assistant" and msg["content"].startswith("### 📝 AI 생성 특허 청구항"))
                            ]

                            claim_msg = "### 📝 AI 생성 특허 청구항\n\n"
                            claim_msg += "#### 🔹 독립항 (제1항)\n"
                            claim_msg += f"{generated.get('claim_1', '')}\n\n"
                            claim_msg += "#### 🔸 종속항 (제2항 ~)\n"
                            claim_msg += f"{generated.get('dependent_claims', '')}"
                            
                            st.session_state.messages.append({"role": "assistant", "content": claim_msg})
                            st.rerun() 
                        else:
                            st.error(f"청구항 생성에 실패했습니다: {generated['error']}")


# ─────────────────────────────────────────────
# 7. 도면 에이전트 연결
# ─────────────────────────────────────────────
import sys as _sys
_REPO_ROOT = _ENV_DIR.parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.append(str(_REPO_ROOT))
from drawing_agent import generate_all_drawings
from drawing_db import save_drawings_to_db

if "drawing_results" not in st.session_state:
    st.session_state.drawing_results = None
if "drawing_save_msg" not in st.session_state:
    st.session_state.drawing_save_msg = None

def _build_invention_text(state):
    parts = []
    for key, label in [
        ("problem",         "[기존 기술의 문제점]"),
        ("solution",        "[해결 방법]"),
        ("differentiation", "[차별성]"),
        ("effect",          "[기대효과]"),
    ]:
        if state.get(key):
            parts.append(f"{label}\n{state[key]}")
    if state.get("algorithm_steps"):
        steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(state["algorithm_steps"]))
        parts.append(f"[작동 알고리즘]\n{steps}")
    for key, label in [
        ("implementations",  "[구현수단]"),
        ("parameters",       "[파라미터/데이터]"),
        ("algorithms",       "[핵심 알고리즘]"),
        ("optional_features","[부가기능]"),
        ("error_handling",   "[예외처리]"),
    ]:
        items = [x for x in state.get(key, []) if x]
        if items:
            parts.append(label + "\n" + "\n".join(f"- {x}" for x in items))
    return "\n\n".join(parts)

# 사이드바: 도면 생성 버튼 (청구항 이후)
if st.session_state.agent and st.session_state.prior_art_result:
    with st.sidebar:
        st.divider()
        st.subheader("🎨 특허 도면 생성")

        _claim_ok = (
            st.session_state.generated_claim
            and isinstance(st.session_state.generated_claim, dict)
            and "error" not in st.session_state.generated_claim
        )

        if not _claim_ok:
            st.warning("⚠️ 도면을 생성하려면 먼저 위의 '청구항 생성' 버튼을 눌러주세요.")
        else:
            if st.button("🎨 특허 도면 자동 생성", use_container_width=True, type="primary"):
                with st.spinner("특허 도면을 생성 중입니다... (1~2분 소요)"):
                    _invention_text = _build_invention_text(st.session_state.agent.state)
                    _app_num = f"{st.session_state.agent.user_id}_{st.session_state.agent.consultation_idx}"
                    _output_dir = str(_REPO_ROOT / "drawing_analysis")
                    try:
                        _results = generate_all_drawings(
                            invention_text=_invention_text,
                            app_num=_app_num,
                            output_dir=_output_dir,
                            export_svg=True,
                            export_png=True,
                        )
                        st.session_state.drawing_results = _results
                        # DB 저장
                        try:
                            save_drawings_to_db(
                                user_id=st.session_state.agent.user_id,
                                consultation_idx=st.session_state.agent.consultation_idx,
                                drawing_results=_results,
                            )
                            st.session_state.drawing_save_msg = ("success", f"도면 {len(_results)}개 생성 및 DB 저장 완료!")
                        except Exception as _db_err:
                            st.session_state.drawing_save_msg = ("warning", f"도면 {len(_results)}개 생성 완료! (DB 저장 실패: {_db_err})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"도면 생성 오류: {e}")

# 메인 화면: 도면 저장 메시지 표시 (rerun 후)
if st.session_state.get("drawing_save_msg"):
    _msg_type, _msg_text = st.session_state.drawing_save_msg
    if _msg_type == "success":
        st.success(_msg_text)
    else:
        st.warning(_msg_text)
    st.session_state.drawing_save_msg = None

# 메인 화면: 도면 결과 표시
if st.session_state.get("drawing_results"):
    st.markdown("---")
    st.markdown("## 🎨 생성된 특허 도면")
    for _r in st.session_state.drawing_results:
        with st.expander(
            f"📐 {_r.fig_number} — {_r.diagram_title}  (품질: {_r.quality_score}점 / {_r.quality_grade}등급)",
            expanded=True
        ):
            if _r.png_path and Path(_r.png_path).exists():
                st.image(_r.png_path, caption=f"{_r.fig_number}: {_r.diagram_title}")
            elif _r.svg_path and Path(_r.svg_path).exists():
                with open(_r.svg_path, "r", encoding="utf-8") as _f:
                    _svg = _f.read()
                st.markdown(
                    f'<div style="background:white;padding:10px;border-radius:8px">{_svg}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.warning("도면 파일을 찾을 수 없습니다.")
            _c1, _c2, _c3 = st.columns(3)
            _c1.metric("품질 점수", f"{_r.quality_score}점")
            _c2.metric("등급", _r.quality_grade)
            _c3.metric("도면 유형", _r.diagram_type)
