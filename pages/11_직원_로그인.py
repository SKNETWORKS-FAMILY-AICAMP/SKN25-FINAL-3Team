import streamlit as st

st.set_page_config(
    page_title="직원 로그인 | PatentAI",
    page_icon="⚖️",
    layout="centered"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500;600&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #0A0A16;
    font-family: 'Noto Sans KR', sans-serif;
}

header[data-testid="stHeader"] {
    display: none;
}

.block-container {
    max-width: 520px;
    padding-top: 90px;
}

.logo {
    text-align: center;
    font-family: 'Noto Serif KR', serif;
    letter-spacing: .22em;
    color: #F0EDE6;
    font-size: 1.35rem;
    margin-bottom: 2rem;
}

.logo em {
    color: #C9A84C;
    font-style: normal;
}

.login-card {
    background: #F5F4F1;
    border: 1px solid rgba(201,168,76,.35);
    padding: 3rem;
    box-shadow: 0 22px 50px rgba(0,0,0,.28);
}

.kicker {
    color: #C9A84C;
    letter-spacing: .28em;
    font-size: .72rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.login-title {
    font-family: 'Noto Serif KR', serif;
    font-size: 2.1rem;
    font-weight: 300;
    color: #111128;
    margin-bottom: .8rem;
}

.login-sub {
    color: #666;
    line-height: 1.8;
    font-size: .92rem;
    margin-bottom: 2.2rem;
}

.stTextInput label {
    color: #222 !important;
    font-size: .85rem !important;
    font-weight: 600 !important;
}

.stTextInput input {
    border-radius: 0 !important;
    border: 1px solid #D8D2C8 !important;
    height: 48px !important;
}

.stTextInput input:focus {
    border: 1px solid #C9A84C !important;
    box-shadow: 0 0 0 1px #C9A84C !important;
}

.stButton > button {
    width: 100%;
    border-radius: 0;
    background: #111128;
    color: #C9A84C;
    border: 1px solid #111128;
    padding: .8rem;
    font-weight: 700;
    margin-top: .8rem;
}

.stButton > button:hover {
    background: #C9A84C;
    color: #111128;
    border-color: #C9A84C;
}

.help {
    margin-top: 1.5rem;
    padding-top: 1.2rem;
    border-top: 1px solid #DDD4C4;
    color: #777;
    font-size: .82rem;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="logo">PATENT<em>AI</em></div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="login-card">
    <div class="kicker">STAFF ACCESS</div>
    <div class="login-title">직원 로그인</div>
    <div class="login-sub">
        PatentAI 내부 직원 전용 페이지입니다.<br>
        상담 관리와 AI 분석 시스템에 접근할 수 있습니다.
    </div>
</div>
""", unsafe_allow_html=True)

staff_id = st.text_input("직원 아이디", placeholder="직원 아이디 또는 이메일")
password = st.text_input("비밀번호", type="password", placeholder="비밀번호")

if st.button("로그인"):
    st.success("직원 로그인 버튼 클릭됨")

st.markdown("""
<div class="help">
    내부 직원만 접근 가능한 페이지입니다.<br>
    계정 문의는 관리자에게 문의하세요.
</div>
""", unsafe_allow_html=True)