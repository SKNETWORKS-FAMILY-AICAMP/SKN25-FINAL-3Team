import json
import sys
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.specification import (
    run_specification_agent,
    SpecificationAgentConfig,
    convert_to_markdown_format,
    save_specification,
    get_specification_markdown_path,
    load_specification_markdown,
)
from agents.schemas.specification import SpecificationAgentOutput

# ─────────────────────────────────────────────
# 1. 페이지 설정 및 프리미엄 스타일링 (CSS)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Patent AI | Specification Agent Playground",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Stunning Dark Cyber Aesthetics
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #1e1b4b 100%);
        color: #f3f4f6;
    }
    
    .premium-title {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.1rem;
        letter-spacing: -0.05rem;
    }
    
    .premium-subtitle {
        color: #9ca3af;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .glass-card {
        background: rgba(17, 24, 39, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.8rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    .section-header {
        border-left: 4px solid #818cf8;
        padding-left: 0.75rem;
        margin-top: 1.8rem;
        margin-bottom: 1rem;
        font-weight: 700;
        font-size: 1.3rem;
        color: #f3f4f6;
    }
    
    /* Input field background */
    div[data-baseweb="input"], div[data-baseweb="textarea"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #f3f4f6 !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(31, 41, 55, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 8px 8px 0px 0px !important;
        padding: 10px 22px !important;
        color: #9ca3af !important;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, rgba(99, 102, 241, 0.3), rgba(124, 58, 237, 0.3)) !important;
        border-bottom: 2px solid #818cf8 !important;
        color: #ffffff !important;
    }
    
    .saved-path {
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        color: #34d399;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 2. 헤더 및 레이아웃 정의
# ─────────────────────────────────────────────
st.markdown("<div class='premium-title'>✍️ Specification Agent Playground</div>", unsafe_allow_html=True)
st.markdown("<div class='premium-subtitle'>특허 명세서(발명의 설명) 생성 엔진 & 마크다운 파일 저장 시스템</div>", unsafe_allow_html=True)

# 세션 상태 변수 초기화
if "spec_output" not in st.session_state: st.session_state.spec_output = None
if "invention_title" not in st.session_state: st.session_state.invention_title = ""
if "last_saved_paths" not in st.session_state: st.session_state.last_saved_paths = None
if "loaded_markdown" not in st.session_state: st.session_state.loaded_markdown = None

# 두 개의 탭 구성
tab_exec, tab_history = st.tabs(["🤖 명세서 에이전트 실행", "📂 저장된 명세서 이력 조회"])

# ─────────────────────────────────────────────
# 3. 탭 1: 명세서 에이전트 실행 및 저장
# ─────────────────────────────────────────────
with tab_exec:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("<div class='section-header'>⚙️ 실행 설정</div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            uploaded_file = st.file_uploader("테스트용 state JSON 업로드", type=["json"])
            
            model = st.text_input("OpenAI 모델명", value="gpt-5.1")
            
            user_id = st.text_input("사용자 ID (user_id)", value="test_user")
            
            consultation_idx = st.number_input("상담 회차 (consultation_idx)", value=1, min_value=1, step=1)
            
            # JSON 저장 유무 선택 옵션
            save_json_opt = st.checkbox("JSON 파일 함께 저장 (save_json=True)", value=False)
            
            execute_btn = st.button("🚀 명세서 에이전트 실행", use_container_width=True)

    with col_right:
        st.markdown("<div class='section-header'>📊 에이전트 실행 및 저장 제어</div>", unsafe_allow_html=True)
        
        if uploaded_file:
            state = json.load(uploaded_file)
            
            # 필수 옵션 사전 기본값 구성
            if "drafting_options" not in state:
                state["drafting_options"] = {
                    "use_subheadings_in_detailed_description": False,
                    "brief_drawing_description": True,
                    "strict_grounding": True,
                    "avoid_reference_numerals_in_means": True
                }
                
            inv_title = state.get("consultation", {}).get("invention_title") or "발명의 명칭 미정"
            st.session_state.invention_title = inv_title

            with st.container(border=True):
                st.write(f"📝 **가져온 발명 명칭**: {inv_title}")
                st.write(f"📌 **청구항 수**: {len(state.get("claims", {}).get("draft_claims", []))}개 | **도면 수**: {len(state.get("drawings", {}).get("figures", []))}개")

            if execute_btn:
                config = SpecificationAgentConfig(model=model)
                with st.spinner("전문 AI 변리사가 명세서 본문을 생성하고 있습니다..."):
                    raw_output = run_specification_agent(state, config=config)
                    st.session_state.spec_output = SpecificationAgentOutput.model_validate(raw_output)
                    st.session_state.last_saved_paths = None  # 신규 실행 시 이전 저장 정보 리셋
                    st.success("명세서 생성 성공!")

            # 생성된 결과가 세션에 존재할 때만 제어 패널 노출
            if st.session_state.spec_output:
                validated = st.session_state.spec_output
                st.markdown("<div class='section-header'>💾 저장 및 다운로드</div>", unsafe_allow_html=True)
                
                # 저장 버튼 및 마크다운 다운로드 버튼 나란히 배치
                btn_col1, btn_col2 = st.columns(2)
                
                with btn_col1:
                    if st.button("💾 로컬에 마크다운 파일로 저장", use_container_width=True):
                        # specification_storage의 save_specification 유틸리티 호출
                        paths = save_specification(
                            user_id=user_id,
                            consultation_idx=consultation_idx,
                            spec_dict=validated.model_dump(),
                            invention_title=st.session_state.invention_title,
                            save_json=save_json_opt,
                        )
                        st.session_state.last_saved_paths = paths
                        st.balloons()
                
                # 마크다운 렌더링 후 다운로드 버튼 연결
                md_content = convert_to_markdown_format(st.session_state.invention_title, validated.model_dump())
                
                with btn_col2:
                    st.download_button(
                        label="⬇️ 명세서 마크다운(.md) 즉시 다운로드",
                        data=md_content,
                        file_name=f"specification_{user_id}_{consultation_idx}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

                # 파일 저장 완료 시 경로 표기
                if st.session_state.last_saved_paths:
                    paths = st.session_state.last_saved_paths
                    st.markdown("<div class='section-header'>📁 로컬 저장 완료 정보</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class='saved-path'>
                    🟢 <b>Markdown 저장 경로:</b> {paths['markdown_path']}<br>
                    {'🟢 <b>JSON 저장 경로:</b> ' + paths['json_path'] if 'json_path' in paths else '⚠️ <b>JSON 저장:</b> 미활성화 (옵션 체크 필요)'}
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.info("💡 왼쪽에 테스트용 `state JSON` 파일을 업로드한 후 에이전트를 실행해 주세요.")

    # 하단 전체 영역: 생성된 명세서 미리보기
    if st.session_state.spec_output:
        validated = st.session_state.spec_output
        st.markdown("<div class='section-header'>👁️ 생성된 명세서 미리보기</div>", unsafe_allow_html=True)
        
        # 아름다운 탭 또는 아코디언 형태로 각 섹션 렌더링
        sec_tabs = st.tabs([
            "전체 마크다운", "1. 기술분야", "2. 배경기술", 
            "3. 해결과제", "4. 해결수단", "5. 발명효과", 
            "6. 도면설명", "7. 구체적내용", "🔍 검증"
        ])
        
        with sec_tabs[0]:
            md_content = convert_to_markdown_format(st.session_state.invention_title, validated.model_dump())
            st.markdown(f"```markdown\n{md_content}\n```")
            
        with sec_tabs[1]:
            st.markdown(validated.technical_field)
        with sec_tabs[2]:
            st.markdown(validated.background_art)
        with sec_tabs[3]:
            st.markdown(validated.problem_to_solve)
        with sec_tabs[4]:
            st.markdown(validated.means_for_solving)
        with sec_tabs[5]:
            st.markdown(validated.effects)
        with sec_tabs[6]:
            st.markdown(validated.brief_description_of_drawings)
        with sec_tabs[7]:
            st.markdown(validated.detailed_description)
        with sec_tabs[8]:
            st.subheader("검증 결과 (Validation Results)")
            st.json(validated.details.get("validation", {}))
            st.subheader("Support Matrix")
            st.dataframe(validated.details.get("support_matrix", []))

# ─────────────────────────────────────────────
# 4. 탭 2: 저장된 명세서 이력 조회 (Load & Display)
# ─────────────────────────────────────────────
with tab_history:
    st.markdown("<div class='section-header'>📂 저장된 명세서 로드</div>", unsafe_allow_html=True)
    
    hist_col1, hist_col2, hist_col3 = st.columns([1, 1, 2])
    
    with hist_col1:
        hist_user_id = st.text_input("조회할 사용자 ID", value="test_user", key="hist_uid")
    with hist_col2:
        hist_idx = st.number_input("조회할 상담 회차", value=1, min_value=1, step=1, key="hist_idx")
        
    with hist_col3:
        st.write("")
        st.write("")
        load_btn = st.button("📂 로컬 파일에서 명세서 불러오기", use_container_width=True)

    if load_btn:
        try:
            # specification_storage의 load_specification_markdown 유틸리티 호출
            loaded_md = load_specification_markdown(hist_user_id, hist_idx)
            st.session_state.loaded_markdown = loaded_md
            st.success("성공적으로 명세서 마크다운 파일을 불러왔습니다!")
        except FileNotFoundError as e:
            st.session_state.loaded_markdown = None
            st.error(f"❌ 불러오기 실패: {str(e)}")
        except Exception as e:
            st.session_state.loaded_markdown = None
            st.error(f"❌ 예기치 못한 오류 발생: {str(e)}")

    if st.session_state.loaded_markdown:
        loaded_md_content = st.session_state.loaded_markdown
        
        st.markdown("<div class='section-header'>📄 불러온 명세서 마크다운 렌더링</div>", unsafe_allow_html=True)
        
        # 파일 기반 다운로드 버튼 함께 제공
        st.download_button(
            label="⬇️ 불러온 마크다운(.md) 파일 다운로드",
            data=loaded_md_content,
            file_name=f"loaded_specification_{hist_user_id}_{hist_idx}.md",
            mime="text/markdown",
        )
        
        # 마크다운 렌더링
        with st.container(border=True):
            st.markdown(loaded_md_content)