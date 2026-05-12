import streamlit as st
import streamlit.components.v1 as components


def setup_page(title="PatentAI"):
    st.set_page_config(
        page_title=title,
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
<style>
html, body, .stApp {
    margin: 0 !important;
    padding: 0 !important;
    background: #0A0A16 !important;
}

header[data-testid="stHeader"],
section[data-testid="stSidebar"],
div[data-testid="stSidebarNav"] {
    display: none !important;
}

.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

.element-container {
    margin: 0 !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)


def render_html(html: str):
    if hasattr(st, "html"):
        st.html(html)
    else:
        components.html(html, height=2200, scrolling=True)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500;600&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

* { box-sizing: border-box; }
a { text-decoration: none; }

.site {
    width: 100%;
    min-height: 100vh;
    background: #F5F4F1;
    font-family: 'Noto Sans KR', sans-serif;
    color: #1A1A2E;
}

.nav {
    width: 100%;
    height: 74px;
    background: #0A0A16;
    display: flex;
    align-items: center;
    padding: 0 2.4rem;
    border-bottom: 1px solid rgba(201,168,76,.25);
}

.logo {
    font-family: 'Noto Serif KR', serif;
    color: #F0EDE6;
    letter-spacing: .2em;
    font-size: 1.05rem;
    margin-right: 3rem;
    white-space: nowrap;
}

.logo em {
    color: #C9A84C;
    font-style: normal;
}

.logo span {
    color: #7777A0;
    font-size: .7rem;
    margin-left: .8rem;
    letter-spacing: .08em;
}

.menu {
    display: flex;
    gap: 1.6rem;
    align-items: center;
    flex: 1;
}

.menu a {
    color: #C8C8D8;
    font-size: .78rem;
    font-weight: 600;
}

.menu a:hover {
    color: #C9A84C;
}

.nav-actions {
    display: flex;
    gap: .7rem;
    margin-left: auto;
}

.login-btn {
    height: 34px;
    padding: 0 .95rem;
    border: 1px solid rgba(201,168,76,.45);
    color: #C8C8D8;
    display: flex;
    align-items: center;
    font-size: .72rem;
    white-space: nowrap;
}

.login-btn:hover {
    color: #111128;
    background: #C9A84C;
    border-color: #C9A84C;
}

.hero {
    background: #111128;
    padding: 7rem 5.5rem;
    color: white;
    border-bottom: 2px solid #C9A84C;
}

.hero.home {
    position: relative;
    height: 720px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    overflow: hidden;
    background: #0A0A16;
    padding: 0;
}

.hero-slide {
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    opacity: 0;
    animation: heroFade 15s infinite;
    filter: brightness(.48) saturate(.95);
}

.hero-slide:nth-child(1) {
    background-image:
        linear-gradient(rgba(10,10,22,.25), rgba(10,10,22,.88)),
        url('https://commons.wikimedia.org/wiki/Special:FilePath/N%20Seoul%20Tower%20%2813952097192%29.jpg');
    animation-delay: 0s;
}

.hero-slide:nth-child(2) {
    background-image:
        linear-gradient(rgba(10,10,22,.25), rgba(10,10,22,.88)),
        url('https://commons.wikimedia.org/wiki/Special:FilePath/Lotte%20World%20Tower%20%2822074455581%29.jpg');
    animation-delay: 5s;
}

.hero-slide:nth-child(3) {
    background-image:
        linear-gradient(rgba(10,10,22,.25), rgba(10,10,22,.88)),
        url('https://commons.wikimedia.org/wiki/Special:FilePath/Gwanghwamun%20Plaza%2C%20Seoul.jpg');
    animation-delay: 10s;
}

@keyframes heroFade {
    0% { opacity: 0; transform: scale(1.03); }
    8% { opacity: 1; }
    33% { opacity: 1; }
    41% { opacity: 0; transform: scale(1.08); }
    100% { opacity: 0; }
}

.hero-content {
    position: relative;
    z-index: 2;
}

.tag {
    color: #C9A84C;
    letter-spacing: .35em;
    font-size: .72rem;
    margin-bottom: 1rem;
    text-transform: uppercase;
}

.hero h1 {
    font-family: 'Noto Serif KR', serif;
    font-size: 3.2rem;
    font-weight: 300;
    line-height: 1.45;
    margin: 0;
}

.hero.home h1 {
    font-size: 3.45rem;
}

.hero p {
    color: #AAAAC0;
    margin-top: 1.2rem;
    line-height: 1.8;
    font-size: .98rem;
}

.hero.home p {
    color: #D7D7E2;
}

.line,
.sec-line {
    width: 40px;
    height: 2px;
    background: #C9A84C;
    margin-bottom: 1rem;
}

.hero.home .line {
    margin: 1.5rem auto;
}

.btn {
    display: inline-block;
    margin-top: 2rem;
    padding: .9rem 2.8rem;
    border: 1px solid #C9A84C;
    color: #C9A84C;
    font-size: .82rem;
    letter-spacing: .12em;
}

.btn:hover {
    background: #C9A84C;
    color: #111128;
}

.stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
}

.stat {
    background: #111128;
    text-align: center;
    padding: 2.2rem 1rem;
    border-right: 1px solid rgba(201,168,76,.18);
}

.stat b {
    color: #C9A84C;
    font-family: 'Noto Serif KR', serif;
    font-size: 2.4rem;
    font-weight: 300;
}

.stat p {
    color: #B8B8C8;
    font-size: .75rem;
    margin-top: .4rem;
}

.section {
    padding: 4.5rem 5.5rem;
    background: #F5F4F1;
}

.section.dark {
    background: #111128;
    color: #F5F0E8;
}

.title,
.sec-title {
    font-family: 'Noto Serif KR', serif;
    font-size: 2.1rem;
    font-weight: 300;
    margin-bottom: .7rem;
    color: #1A1A2E;
}

.dark .title,
.dark .sec-title {
    color: #F5F0E8;
}

.sub,
.sec-sub {
    color: #666;
    line-height: 1.8;
    margin-bottom: 2.2rem;
}

.dark .sub,
.dark .sec-sub {
    color: #AAAAC0;
}

.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.4rem;
}

.card,
.member,
.news {
    background: white;
    border: 1px solid #E8E4DC;
    padding: 2rem;
    min-height: 250px;
    box-shadow: 0 12px 30px rgba(0,0,0,.04);
    transition: .2s;
}

.card:hover,
.member:hover,
.news:hover {
    transform: translateY(-5px);
    box-shadow: 0 18px 38px rgba(0,0,0,.09);
}

.num {
    font-family: 'Noto Serif KR', serif;
    color: #C9A84C;
    font-size: 2rem;
    margin-bottom: 1rem;
}

.card h3,
.news h3 {
    color: #1A1A2E;
    margin-bottom: .8rem;
    font-size: 1.08rem;
}

.card p,
.news p,
.desc {
    color: #666;
    line-height: 1.75;
    font-size: .9rem;
}

.avatar {
    width: 112px;
    height: 112px;
    border-radius: 50%;
    background: linear-gradient(135deg,#1A1A2E,#C9A84C);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-family: 'Noto Serif KR', serif;
    font-size: 2.1rem;
    margin-bottom: 1.3rem;
}

.name {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: .45rem;
}

.role {
    color: #C9A84C;
    font-size: .86rem;
    margin-bottom: .9rem;
}

.thumb {
    height: 190px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#111128,#C9A84C);
    color: white;
    font-family: 'Noto Serif KR', serif;
    font-size: 2rem;
    margin: -2rem -2rem 1.6rem;
}

.category {
    color: #C9A84C;
    font-size: .72rem;
    letter-spacing: .16em;
    margin-bottom: .7rem;
}

.workflow {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: .9rem;
}

.step {
    border: 1px solid rgba(201,168,76,.3);
    padding: 1.5rem;
    background: rgba(255,255,255,.04);
}

.step b {
    color: #C9A84C;
    font-family: 'Noto Serif KR', serif;
    font-size: 1.5rem;
}

.step p {
    margin-top: .8rem;
    color: #F5F0E8;
    font-size: .9rem;
}

.footer {
    background: #0A0A16;
    color: #7777A0;
    padding: 2.5rem 5rem;
    border-top: 1px solid rgba(201,168,76,.18);
    font-size: .78rem;
}

@media (max-width: 900px) {
    .nav {
        padding: 0 1rem;
        overflow-x: auto;
    }

    .logo span {
        display: none;
    }

    .nav-actions {
        display: none;
    }

    .grid,
    .stats,
    .workflow {
        grid-template-columns: 1fr;
    }

    .section,
    .hero {
        padding: 4rem 1.5rem;
    }

    .hero.home {
        height: 640px;
        padding: 0 1.5rem;
    }

    .hero h1,
    .hero.home h1 {
        font-size: 2.3rem;
    }
}
</style>
"""

NAV = """
<div class="nav">
    <a class="logo" href="/" target="_self">PATENT<em>AI</em><span>지식재산 상담 시스템</span></a>

    <div class="menu">
        <a href="/" target="_self">홈</a>
        <a href="/서비스_소개" target="_self">서비스 소개</a>
        <a href="/구성원" target="_self">구성원</a>
        <a href="/소식_자료" target="_self">소식/자료</a>
    </div>

    <div class="nav-actions">
        <a class="login-btn" href="#" target="_self">고객 로그인</a>
        <a class="login-btn" href="#" target="_self">직원 로그인</a>
    </div>
</div>
"""

FOOTER = """
<div class="footer">
    PATENTAI · 지식재산 상담 시스템<br>
    © 2026 PatentAI. All rights reserved.
</div>
"""


def render_home():
    html = CSS + f"""
<div class="site">
    {NAV}

    <div class="hero home">
        <div class="hero-slide"></div>
        <div class="hero-slide"></div>
        <div class="hero-slide"></div>

        <div class="hero-content">
            <div class="tag">AI-POWERED PATENT CONSULTATION SYSTEM</div>
            <h1>발명의 가치를<br>권리로 만들어 드립니다</h1>
            <div class="line"></div>
            <p>
                발명 내용을 자유롭게 설명해 주시면<br>
                AI가 특허 출원에 필요한 정보를 체계적으로 구조화해 드립니다
            </p>
            <a class="btn" href="/서비스_소개" target="_self">서비스 살펴보기 →</a>
        </div>
    </div>

    <div class="stats">
        <div class="stat"><b>1,240+</b><p>처리 특허 건수</p></div>
        <div class="stat"><b>98.2%</b><p>고객 만족도</p></div>
        <div class="stat"><b>12</b><p>AI 전문 모델</p></div>
        <div class="stat"><b>542+</b><p>학습 특허 데이터</p></div>
    </div>

    <div class="section">
        <div class="sec-line"></div>
        <div class="sec-title">주요 서비스</div>
        <div class="sec-sub">AI 기반 특허 출원 전 과정을 지원합니다.</div>

        <div class="grid">
            <a href="/서비스_소개" target="_self">
                <div class="card">
                    <div class="num">01</div>
                    <h3>선행기술 조사</h3>
                    <p>발명 내용을 기반으로 유사 특허와 선행기술을 자동으로 탐색합니다.</p>
                </div>
            </a>

            <a href="/서비스_소개" target="_self">
                <div class="card">
                    <div class="num">02</div>
                    <h3>명세서 작성</h3>
                    <p>청구항, 발명의 설명, 도면 설명을 구조화하여 초안을 생성합니다.</p>
                </div>
            </a>

            <a href="/서비스_소개" target="_self">
                <div class="card">
                    <div class="num">03</div>
                    <h3>도면 에이전트</h3>
                    <p>특허 명세서를 분석하여 블록도와 흐름도를 자동 생성합니다.</p>
                </div>
            </a>
        </div>
    </div>

    <div class="section dark">
        <div class="sec-line"></div>
        <div class="sec-title">PatentAI 업무 흐름</div>
        <div class="sec-sub">발명 상담부터 도면 생성과 검토까지 하나의 흐름으로 연결합니다.</div>

        <div class="workflow">
            <div class="step"><b>01</b><p>발명 내용 입력</p></div>
            <div class="step"><b>02</b><p>AI 구조화</p></div>
            <div class="step"><b>03</b><p>선행기술 분석</p></div>
            <div class="step"><b>04</b><p>명세서/도면 생성</p></div>
            <div class="step"><b>05</b><p>검토 및 리포트</p></div>
        </div>
    </div>

    {FOOTER}
</div>
"""
    render_html(html)


def render_service():
    html = CSS + f"""
<div class="site">
    {NAV}

    <div class="hero">
        <div class="tag">SERVICE OVERVIEW</div>
        <h1>AI 기반 특허 출원 서비스를<br>하나의 흐름으로 제공합니다</h1>
        <p>
            PatentAI는 발명 상담, 선행기술 조사, 명세서 작성, 도면 생성, 검토까지<br>
            특허 출원 전 과정을 자동화하는 지식재산 상담 시스템입니다.
        </p>
    </div>

    <div class="section">
        <div class="line"></div>
        <div class="title">PatentAI 핵심 서비스</div>
        <div class="sub">변리사 업무 흐름을 기준으로 필요한 절차를 단계별 AI 에이전트로 구성했습니다.</div>

        <div class="grid">
            <div class="card">
                <div class="num">01</div>
                <h3>특허 상담 에이전트</h3>
                <p>사용자의 발명 설명을 바탕으로 문제점, 해결수단, 효과, 구성요소를 구조화합니다.</p>
            </div>

            <div class="card">
                <div class="num">02</div>
                <h3>선행기술 조사</h3>
                <p>유사 특허와 기존 기술을 분석하여 신규성 및 진보성 리스크를 빠르게 파악합니다.</p>
            </div>

            <div class="card">
                <div class="num">03</div>
                <h3>명세서 작성</h3>
                <p>청구항, 발명의 설명, 실시예, 도면 설명을 자동으로 초안화합니다.</p>
            </div>
        </div>
    </div>

    <div class="section dark">
        <div class="line"></div>
        <div class="title">서비스 차별점</div>
        <div class="sub">단순 문서 생성이 아니라 특허 실무 프로세스에 맞춘 AI 워크플로우를 제공합니다.</div>

        <div class="grid">
            <div class="card">
                <div class="num">A</div>
                <h3>특허 데이터 기반</h3>
                <p>실제 특허 문서 구조를 기반으로 발명 내용을 정리합니다.</p>
            </div>

            <div class="card">
                <div class="num">B</div>
                <h3>도면 자동화</h3>
                <p>명세서 내용을 분석하여 블록도와 흐름도를 자동 생성합니다.</p>
            </div>

            <div class="card">
                <div class="num">C</div>
                <h3>검토 리포트</h3>
                <p>신규성, 진보성, 기재불비 관점에서 검토 결과를 제공합니다.</p>
            </div>
        </div>
    </div>

    {FOOTER}
</div>
"""
    render_html(html)


def render_team():
    members = [
        ("01", "김서현", "Frontend / PatentAI UI", "홈페이지 UI, 다국어 전환, Streamlit 화면 구성, 도면 에이전트 연동을 담당합니다."),
        ("02", "팀원 2", "Prior Art Agent", "선행기술 조사, 특허 데이터 검색, 유사도 분석 기능을 담당합니다."),
        ("03", "팀원 3", "Consultation Agent", "발명 상담 흐름, 상담 로그 구조화, 발명 요약 기능을 담당합니다."),
        ("04", "팀원 4", "Specification Agent", "청구항, 명세서 초안, 발명의 효과 및 구성요소 정리 기능을 담당합니다."),
        ("05", "팀원 5", "Drawing Agent", "특허 도면 자동 생성, Mermaid 변환, SVG/PNG 렌더링 기능을 담당합니다."),
        ("06", "팀원 6", "Review / Integration", "검토 에이전트, 전체 서비스 통합, 테스트 및 발표 자료 정리를 담당합니다."),
    ]

    cards = ""
    for num, name, role, desc in members:
        cards += f"""
        <div class="member">
            <div class="avatar">{num}</div>
            <div class="name">{name}</div>
            <div class="role">{role}</div>
            <div class="desc">{desc}</div>
        </div>
        """

    html = CSS + f"""
<div class="site">
    {NAV}

    <div class="hero">
        <div class="tag">OUR TEAM</div>
        <h1>구성원 소개</h1>
        <p>PatentAI 프로젝트를 함께 개발하는 팀원을 소개합니다.</p>
    </div>

    <div class="section">
        <div class="line"></div>
        <div class="title">PatentAI Team</div>
        <div class="sub">특허 상담, 선행기술 조사, 명세서 작성, 도면 생성, 검토 에이전트를 함께 구축합니다.</div>

        <div class="grid">
            {cards}
        </div>
    </div>

    {FOOTER}
</div>
"""
    render_html(html)


def render_news():
    items = [
        ("01", "AI PATENT", "AI 특허 자동화 확대", "생성형 AI를 활용한 특허 상담, 분석, 명세서 작성 자동화가 확대되고 있습니다."),
        ("02", "PRIOR ART", "선행기술 조사 고도화", "대규모 특허 데이터를 기반으로 유사 기술과 신규성 위험을 빠르게 검토합니다."),
        ("03", "DRAWING", "도면 자동 생성 기술", "명세서의 구성요소와 처리 흐름을 분석해 특허 도면을 자동 구성합니다."),
        ("04", "REVIEW", "심사 대응 자동화", "거절이유를 분석하고 의견서와 보정 방향을 AI가 제안합니다."),
        ("05", "CLAIMS", "청구항 구조 분석", "독립항과 종속항의 관계를 파악하고 권리범위를 구조화합니다."),
        ("06", "IPC / CPC", "IPC 분류 추천", "기술 내용을 분석하여 적합한 IPC/CPC 분류를 추천합니다."),
    ]

    cards = ""
    for num, category, title, desc in items:
        cards += f"""
        <div class="news">
            <div class="thumb">{num}</div>
            <div class="category">{category}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """

    html = CSS + f"""
<div class="site">
    {NAV}

    <div class="hero">
        <div class="tag">NEWS & INSIGHTS</div>
        <h1>소식 / 자료</h1>
        <p>AI 특허 자동화, 선행기술 조사, 명세서 작성 관련 주요 자료를 제공합니다.</p>
    </div>

    <div class="section">
        <div class="line"></div>
        <div class="title">PatentAI 카드뉴스</div>
        <div class="sub">최근 주요 특허 이슈와 AI 기술 동향을 확인하세요.</div>

        <div class="grid">
            {cards}
        </div>
    </div>

    {FOOTER}
</div>
"""
    render_html(html)