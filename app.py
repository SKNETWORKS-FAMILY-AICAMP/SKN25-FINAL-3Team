
import os
import uuid
import importlib
from pathlib import Path
from html import escape

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="PatentAI", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

LANGUAGES = {"ko": "한국어", "en": "English", "zh": "中文", "ja": "日本語"}

NAV_ITEMS = [
    ("home", "nav_home", []),
    ("about", "nav_about", ["nav_about_intro", "nav_about_guide", "nav_about_pricing", "nav_about_faq"]),
    ("consultation", "nav_consultation", ["nav_consult_invention", "nav_consult_strategy", "nav_consult_history"]),
    ("prior_art", "nav_prior_art", ["nav_prior_auto", "nav_prior_similar", "nav_prior_report"]),
    ("specification", "nav_specification", ["nav_claims", "nav_drawing", "nav_spec_draft"]),
    ("drawing", "nav_drawing_agent", ["nav_drawing_create", "nav_drawing_batch", "nav_drawing_history"]),
    ("review", "nav_review", ["nav_review_novelty", "nav_review_inventive", "nav_review_clarity", "nav_review_examiner"]),
    ("request", "nav_request", ["nav_request_online", "nav_request_visit", "nav_request_history"]),
    ("team", "nav_team", ["nav_team_intro", "nav_team_expertise", "nav_team_awards"]),
    ("news", "nav_news", ["nav_news_patent", "nav_news_cases", "nav_news_seminar"]),
]

BASE_KO = {
    "site_sub": "지식재산 상담 시스템",
    "login_member": "회원 로그인",
    "login_staff": "직원 로그인",
    "nav_home": "홈", "nav_about": "서비스 소개", "nav_about_intro": "PatentAI 소개", "nav_about_guide": "이용 안내", "nav_about_pricing": "요금제", "nav_about_faq": "자주 묻는 질문",
    "nav_consultation": "특허 상담", "nav_consult_invention": "발명 내용 상담", "nav_consult_strategy": "출원 전략 수립", "nav_consult_history": "상담 이력 조회",
    "nav_prior_art": "선행기술 조사", "nav_prior_auto": "자동 선행기술 검색", "nav_prior_similar": "유사 특허 분석", "nav_prior_report": "리스크 리포트",
    "nav_specification": "명세서 작성", "nav_claims": "청구항 자동 생성", "nav_drawing": "도면 자동 작성", "nav_spec_draft": "명세서 초안 생성",
    "nav_drawing_agent": "도면 에이전트", "nav_drawing_create": "도면 생성", "nav_drawing_batch": "배치 처리", "nav_drawing_history": "도면 이력",
    "nav_review": "검토 에이전트", "nav_review_novelty": "신규성 검토", "nav_review_inventive": "진보성 검토", "nav_review_clarity": "기재불비 검토", "nav_review_examiner": "심사관 관점 분석",
    "nav_request": "상담 신청", "nav_request_online": "온라인 상담 신청", "nav_request_visit": "방문 상담 예약", "nav_request_history": "상담 이력 조회",
    "nav_team": "구성원", "nav_team_intro": "팀 소개", "nav_team_expertise": "전문 분야", "nav_team_awards": "수상 및 실적",
    "nav_news": "소식/자료", "nav_news_patent": "최신 특허 뉴스", "nav_news_cases": "판례 분석", "nav_news_seminar": "세미나 자료",
    "hero_tag": "AI-Powered Patent Consultation System",
    "hero_title": "발명의 가치를<br><strong>권리로 만들어 드립니다</strong>",
    "hero_sub": "발명 내용을 자유롭게 설명해 주시면<br>AI가 특허 출원에 필요한 정보를 체계적으로 구조화해 드립니다",
    "cta": "상담 신청하기",
    "stats_1": "처리 특허 건수", "stats_2": "고객 만족도", "stats_3": "AI 전문 모델", "stats_4": "학습 특허 데이터",
    "services_title": "주요 서비스", "services_sub": "AI 기반 특허 출원 전 과정을 지원합니다",
    "service_1_title": "선행기술 조사", "service_1_desc": "발명 내용을 기반으로 유사 특허와 선행기술을 자동으로 탐색합니다.",
    "service_2_title": "명세서 작성", "service_2_desc": "청구항, 발명의 설명, 도면 설명을 구조화하여 초안을 생성합니다.",
    "service_3_title": "도면 에이전트", "service_3_desc": "특허 명세서를 분석하여 블록도와 흐름도를 자동 생성합니다.",
    "news_title": "최신 특허 카드뉴스", "news_sub": "최근 주요 특허 이슈와 AI 기술 동향을 카드 형태로 확인하세요",
    "news_1_title": "AI 특허 자동화 확대", "news_1_desc": "생성형 AI를 활용한 특허 상담, 분석, 명세서 작성 자동화가 확대되고 있습니다.",
    "news_2_title": "선행기술 조사 고도화", "news_2_desc": "대규모 특허 데이터를 기반으로 유사 기술과 신규성 위험을 빠르게 검토합니다.",
    "news_3_title": "도면 자동 생성 기술", "news_3_desc": "명세서의 구성요소와 처리 흐름을 분석해 특허 도면을 자동 구성합니다.",
    "news_4_title": "심사 대응 자동화", "news_4_desc": "거절이유를 분석하고 의견서와 보정 방향을 AI가 제안합니다.",
    "news_5_title": "청구항 구조 분석", "news_5_desc": "독립항과 종속항의 관계를 파악하고 권리범위를 구조화합니다.",
    "news_6_title": "IPC 분류 추천", "news_6_desc": "기술 내용을 분석하여 적합한 IPC/CPC 분류를 추천합니다.",
    "workflow_title": "PatentAI 업무 흐름", "workflow_sub": "발명 상담부터 도면 생성과 검토까지 하나의 흐름으로 연결합니다.",
    "workflow_1": "발명 내용 입력", "workflow_2": "AI 구조화", "workflow_3": "선행기술 분석", "workflow_4": "명세서/도면 생성", "workflow_5": "검토 및 리포트",
    "request_title": "상담 신청", "request_check": "AI 전문가가 직접 상담을 진행합니다",
    "form_name": "성함", "form_phone": "연락처", "form_email": "이메일", "form_field": "기술 분야", "form_subject": "제목", "form_content": "발명 내용", "form_submit": "상담 신청하기",
    "form_success": "상담 신청이 완료되었습니다. 24시간 내 연락드리겠습니다.", "form_error": "필수 항목을 모두 입력해주세요.",
    "fields": ["AI/머신러닝", "반도체", "소프트웨어", "바이오/의료", "IoT/전자", "기계/화학", "기타"],
    "login_id": "아이디 / 이메일", "login_pw": "비밀번호", "login_btn": "로그인", "login_ready": "로그인 기능은 준비 중입니다.", "login_no_account": "계정이 없으신가요?", "login_request": "상담 신청하기",
    "agent_missing": "해당 에이전트 파일 또는 실행 함수가 아직 연결되지 않았습니다.", "agent_input": "입력 내용", "agent_run": "에이전트 실행", "agent_result": "실행 결과",
    "consultation_title": "특허 상담 에이전트", "consultation_sub": "발명 내용을 상담 형식으로 구조화합니다.",
    "prior_title": "선행기술 조사 에이전트", "prior_sub": "발명 내용을 기반으로 유사 특허와 리스크를 조사합니다.",
    "spec_title": "명세서 작성 에이전트", "spec_sub": "청구항과 명세서 초안 생성을 위한 에이전트 영역입니다.",
    "review_title": "검토 에이전트", "review_sub": "신규성, 진보성, 기재불비 관점에서 검토합니다.",
    "chatbot_title": "PatentAI 상담봇", "chatbot_welcome": "안녕하세요! 궁금하신 점을 알려주세요 😊", "chatbot_ph": "궁금한 점을 입력하세요...",
    "chatbot_default": "더 구체적으로 말씀해 주시겠어요? 예: 선행기술, 명세서, 도면, 상담 신청",
    "chatbot_prior": "선행기술 조사 페이지로 안내해드릴게요.", "chatbot_spec": "명세서 작성 페이지로 안내해드릴게요.", "chatbot_drawing": "도면 생성 에이전트로 안내해드릴게요.", "chatbot_review": "검토 에이전트 페이지로 안내해드릴게요.", "chatbot_request": "상담 신청 페이지로 안내해드릴게요.",
    "drawing_title": "특허 도면 생성 에이전트", "drawing_sub": "특허 명세서를 업로드하면 자동으로 도면을 생성합니다",
    "drawing_upload": "특허 TXT 파일 업로드", "drawing_text": "또는 명세서 직접 입력", "drawing_app_num": "출원번호 / 작업 ID", "drawing_options": "생성 옵션",
    "drawing_svg": "SVG 생성", "drawing_png": "PNG 생성", "drawing_vision": "Vision 검수", "drawing_repair": "품질 미달 자동 보정", "drawing_rounds": "자동 보정 횟수", "drawing_run": "도면 생성 시작",
    "drawing_no_input": "파일을 업로드하거나 명세서 내용을 입력해주세요.", "drawing_running": "도면 생성 중입니다.", "drawing_done": "도면 생성 완료", "drawing_error": "도면 생성 중 오류가 발생했습니다.", "drawing_result": "생성 결과", "download": "다운로드",
    "ready_title": "페이지 준비 중", "ready_body": "이 영역은 동일한 네비게이션, 챗봇, 다국어 구조로 확장할 수 있습니다.",
}

T = {"ko": BASE_KO}
T["en"] = {**BASE_KO, "site_sub": "IP Consultation System", "login_member": "Member Login", "login_staff": "Staff Login", "nav_home": "Home", "nav_about": "About", "nav_consultation": "Consultation", "nav_prior_art": "Prior Art", "nav_specification": "Specification", "nav_drawing_agent": "Drawing Agent", "nav_review": "Review Agent", "nav_request": "Request", "nav_team": "Team", "nav_news": "News", "hero_title": "Turning Your Invention<br><strong>Into Protected Rights</strong>", "hero_sub": "Describe your invention freely<br>and AI will structure the information required for patent filing", "cta": "Get Consultation", "services_title": "Main Services", "services_sub": "AI-powered support for the entire patent filing process", "service_1_title": "Prior Art Search", "service_1_desc": "Automatically search similar patents and prior art based on invention details.", "service_2_title": "Specification Drafting", "service_2_desc": "Generate structured drafts for claims, descriptions, and drawing explanations.", "service_3_title": "Drawing Agent", "service_3_desc": "Analyze patent specifications and generate block diagrams and flowcharts.", "news_title": "Patent Card News", "news_sub": "Recent patent issues and AI technology trends", "drawing_title": "Patent Drawing Agent", "drawing_sub": "Upload a patent specification to automatically generate drawings", "fields": ["AI/Machine Learning", "Semiconductor", "Software", "Bio/Medical", "IoT/Electronics", "Mechanical/Chemical", "Other"]}
T["zh"] = {**BASE_KO, "site_sub": "知识产权咨询系统", "login_member": "会员登录", "login_staff": "员工登录", "nav_home": "首页", "nav_about": "服务介绍", "nav_consultation": "专利咨询", "nav_prior_art": "先行技术调查", "nav_specification": "说明书撰写", "nav_drawing_agent": "附图代理", "nav_review": "审查代理", "nav_request": "咨询申请", "nav_team": "团队成员", "nav_news": "新闻资料", "hero_tag": "AI驱动的专利咨询系统", "hero_title": "将您的发明<br><strong>转化为受保护的权利</strong>", "hero_sub": "自由描述您的发明内容<br>AI将系统化整理专利申请所需信息", "cta": "申请咨询", "services_title": "主要服务", "services_sub": "AI驱动，支持专利申请全流程", "service_1_title": "先行技术调查", "service_2_title": "说明书撰写", "service_3_title": "附图代理", "news_title": "最新专利卡片新闻", "news_sub": "最近主要专利问题与 AI 技术趋势", "drawing_title": "专利附图生成代理", "drawing_sub": "上传专利说明书后自动生成附图", "fields": ["AI/机器学习", "半导体", "软件", "生物/医疗", "IoT/电子", "机械/化学", "其他"]}
T["ja"] = {**BASE_KO, "site_sub": "知的財産相談システム", "login_member": "会員ログイン", "login_staff": "スタッフログイン", "nav_home": "ホーム", "nav_about": "サービス紹介", "nav_consultation": "特許相談", "nav_prior_art": "先行技術調査", "nav_specification": "明細書作成", "nav_drawing_agent": "図面エージェント", "nav_review": "審査エージェント", "nav_request": "相談申請", "nav_team": "メンバー", "nav_news": "ニュース", "hero_tag": "AI搭載特許相談システム", "hero_title": "あなたの発明を<br><strong>権利として守ります</strong>", "hero_sub": "発明内容を自由にご説明ください<br>AIが特許出願に必要な情報を体系的に整理いたします", "cta": "相談申請", "services_title": "主要サービス", "services_sub": "AI搭載で特許出願の全工程をサポート", "service_1_title": "先行技術調査", "service_2_title": "明細書作成", "service_3_title": "図面エージェント", "news_title": "最新特許カードニュース", "news_sub": "最近の主要特許イシューとAI技術動向", "drawing_title": "特許図面生成エージェント", "drawing_sub": "特許明細書をアップロードすると自動で図面を生成します", "fields": ["AI/機械学習", "半導体", "ソフトウェア", "バイオ/医療", "IoT/電子", "機械/化学", "その他"]}

def get_query_value(key, default=None):
    try:
        value = st.query_params.get(key, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value
    except Exception:
        return default

for key, value in {"lang": "ko", "page": "home", "chat_is_open": False, "chat_msgs": [], "sid": str(uuid.uuid4())[:8]}.items():
    if key not in st.session_state:
        st.session_state[key] = value

url_lang = get_query_value("lang", "ko")
url_page = get_query_value("page", "home")
if url_lang in LANGUAGES:
    st.session_state.lang = url_lang
if url_page:
    st.session_state.page = url_page

lang = st.session_state.lang
page = st.session_state.page

def tr(key):
    return T.get(lang, T["ko"]).get(key, T["ko"].get(key, key))

st.markdown('''
<style>
html, body, .stApp { margin:0 !important; padding:0 !important; background:#0A0A16 !important; }
header[data-testid="stHeader"], section[data-testid="stSidebar"] { display:none !important; }
.block-container { padding:0 !important; margin:0 !important; max-width:100% !important; }
[data-testid="stVerticalBlock"] { gap:0 !important; }
.element-container { margin:0 !important; }
.stButton > button { background:#1A1A2E !important; color:#F5F0E8 !important; border:none !important; border-radius:2px !important; }
.stButton > button:hover { background:#C9A84C !important; color:#1A1A2E !important; }
.chat-float { position: fixed; right: 24px; bottom: 24px; z-index: 30000; }
.chat-panel { position: fixed; right: 24px; bottom: 88px; width: 360px; background: #FFFFFF; border: 1px solid #E8E4DC; box-shadow: 0 18px 45px rgba(0,0,0,.22); z-index: 30000; }
.chat-head { background: #1A1A2E; color: #F5F0E8; padding: .9rem 1rem; font-size: .86rem; display: flex; justify-content: space-between; }
.chat-body { padding: 1rem; max-height: 280px; overflow-y: auto; font-size: .82rem; }
.chat-msg { padding: .65rem .75rem; border-radius: 6px; margin-bottom: .65rem; line-height: 1.55; }
.chat-bot { background: #F5F4F1; margin-right: 2rem; }
.chat-user { background: #EFE8D1; margin-left: 2rem; }
</style>
''', unsafe_allow_html=True)

def build_nav_html():
    nav_html = ""
    for page_key, label_key, subs in NAV_ITEMS:
        sub_html = "".join([f'<a href="?page={page_key}&lang={lang}" target="_top">{escape(tr(sub_key))}</a>' for sub_key in subs])
        if subs:
            nav_html += f'<div class="nav-item"><a class="nav-label" href="?page={page_key}&lang={lang}" target="_top">{escape(tr(label_key))}</a><div class="dropdown">{sub_html}</div></div>'
        else:
            nav_html += f'<div class="nav-item"><a class="nav-label" href="?page={page_key}&lang={lang}" target="_top">{escape(tr(label_key))}</a></div>'
    lang_html = "".join([f'<a class="{"active" if code == lang else ""}" href="?page={page}&lang={code}" target="_top">{escape(label)}</a>' for code, label in LANGUAGES.items()])
    return f'<div class="patent-nav-wrap"><div class="patent-nav"><a class="logo" href="?page=home&lang={lang}" target="_top">PATENT<em>AI</em><span>{escape(tr("site_sub"))}</span></a><div class="nav-links">{nav_html}</div><div class="nav-right"><div class="lang-box"><div class="lang-btn">🌐 {escape(LANGUAGES[lang])} ▾</div><div class="lang-dropdown">{lang_html}</div></div><a class="login-link" href="?page=member_login&lang={lang}" target="_top">{escape(tr("login_member"))}</a><a class="login-link" href="?page=staff_login&lang={lang}" target="_top">{escape(tr("login_staff"))}</a></div></div></div>'

COMMON_CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500&family=Noto+Sans+KR:wght@300;400;500;600&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 100%; min-height: 100%; background: #0A0A16; font-family: 'Noto Sans KR', sans-serif; }
a { text-decoration: none; }
.patent-nav-wrap { width: 100%; background: #0A0A16; border-bottom: 1px solid rgba(201,168,76,.22); position: relative; z-index: 9999; }
.patent-nav { width: 100%; height: 74px; background: #0A0A16; display: flex; align-items: stretch; justify-content: space-between; padding: 0 2.4rem; position: relative; z-index: 9999; }
.logo { font-family: 'Noto Serif KR', serif; font-size: 1.05rem; color: #F0EDE6; letter-spacing: .20em; display: flex; align-items: center; white-space: nowrap; }
.logo em { color: #C9A84C; font-style: normal; }
.logo span { font-family: 'Noto Sans KR', sans-serif; font-size: .67rem; color: #7777A0; margin-left: .9rem; letter-spacing: .08em; }
.nav-links { display: flex; align-items: stretch; justify-content: center; flex: 1; margin-left: 2rem; }
.nav-item { position: relative; display: flex; align-items: center; }
.nav-label { height: 74px; display: flex; align-items: center; padding: 0 .82rem; font-size: .74rem; color: #C8C8D8; letter-spacing: .04em; border-bottom: 2px solid transparent; cursor: pointer; white-space: nowrap; transition: all .2s ease; }
.nav-item:hover .nav-label { color: #C9A84C; border-bottom-color: #C9A84C; }
.dropdown { display: none; position: absolute; top: 74px; left: 0; min-width: 205px; background: #0D0D1A; border: 1px solid rgba(201,168,76,.28); border-top: 2px solid #C9A84C; padding: .55rem 0; box-shadow: 0 20px 45px rgba(0,0,0,.55); z-index: 20000; }
.nav-item:hover .dropdown { display: block; }
.dropdown a { display: block; padding: .58rem 1.2rem; font-size: .76rem; color: #AFAFC5; border-left: 2px solid transparent; white-space: nowrap; transition: all .15s ease; }
.dropdown a:hover { color: #C9A84C; background: rgba(201,168,76,.08); border-left-color: #C9A84C; padding-left: 1.55rem; }
.nav-right { display: flex; align-items: center; gap: .55rem; flex-shrink: 0; }
.lang-box { position: relative; }
.lang-btn { height: 34px; padding: 0 .8rem; border: 1px solid rgba(201,168,76,.38); color: #C8C8D8; display: flex; align-items: center; gap: .35rem; font-size: .72rem; white-space: nowrap; cursor: pointer; background: transparent; }
.lang-box:hover .lang-btn { color: #C9A84C; border-color: #C9A84C; }
.lang-dropdown { display: none; position: absolute; top: 34px; right: 0; min-width: 145px; background: #0D0D1A; border: 1px solid rgba(201,168,76,.28); border-top: 2px solid #C9A84C; padding: .45rem 0; box-shadow: 0 18px 42px rgba(0,0,0,.55); z-index: 21000; }
.lang-box:hover .lang-dropdown { display: block; }
.lang-dropdown a { display: block; padding: .58rem 1.1rem; font-size: .76rem; color: #AFAFC5; white-space: nowrap; border-left: 2px solid transparent; }
.lang-dropdown a:hover, .lang-dropdown a.active { color: #C9A84C; background: rgba(201,168,76,.08); border-left-color: #C9A84C; }
.login-link { height: 34px; padding: 0 .85rem; border: 1px solid rgba(201,168,76,.38); color: #C8C8D8; display: flex; align-items: center; font-size: .72rem; white-space: nowrap; }
.login-link:hover { color: #C9A84C; border-color: #C9A84C; }
@media (max-width: 1300px) { .patent-nav { padding: 0 1rem; } .nav-label { padding: 0 .45rem; font-size: .68rem; } .logo span { display: none; } }
'''

HOME_CSS = COMMON_CSS + '''
.hero { position: relative; width: 100%; height: 640px; overflow: hidden; display: flex; align-items: center; justify-content: center; text-align: center; }
.slide { position: absolute; inset: 0; background-size: cover; background-position: center; opacity: 0; transition: opacity 1.2s ease-in-out; filter: brightness(.45) saturate(.9); }
.slide.active { opacity: 1; }
.hero::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgba(8,8,18,.18), rgba(8,8,18,.90)); z-index: 1; }
.hero-content { position: relative; z-index: 2; padding: 0 2rem; }
.hero-tag { font-size: .68rem; letter-spacing: .38em; color: #C9A84C; text-transform: uppercase; margin-bottom: 1.2rem; }
.hero-title { font-family: 'Noto Serif KR', serif; font-size: 3.05rem; font-weight: 300; color: #F0EDE6; line-height: 1.55; }
.hero-title strong { color: #F5F0E8; font-weight: 500; }
.hero-line { width: 38px; height: 1px; background: #C9A84C; margin: 1.25rem auto; }
.hero-sub { color: #D5D5DF; font-size: .95rem; line-height: 1.9; }
.hero-cta { display: inline-block; margin-top: 1.8rem; padding: .8rem 2.4rem; border: 1px solid #C9A84C; color: #C9A84C; letter-spacing: .12em; font-size: .8rem; transition: all .2s ease; }
.hero-cta:hover { background: #C9A84C; color: #1A1A2E; }
.hero-dots { position: absolute; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 3; display: flex; gap: 10px; }
.hero-dot { width: 34px; height: 3px; background: rgba(255,255,255,.35); }
.hero-dot.active { background: #C9A84C; }
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }
.stat-box { background: #111128; border-right: 1px solid rgba(201,168,76,.18); text-align: center; padding: 2rem 1rem; }
.stat-num { font-family: 'Noto Serif KR', serif; color: #C9A84C; font-size: 2.5rem; font-weight: 300; }
.stat-label { color: #B8B8C8; font-size: .75rem; letter-spacing: .1em; margin-top: .4rem; }
.section { background: #F5F4F1; padding: 4rem 5rem; }
.section.alt { background: #ECE9E2; }
.section.dark { background: #111128; }
.sec-line { width: 38px; height: 2px; background: #C9A84C; margin-bottom: 1rem; }
.sec-title { font-family: 'Noto Serif KR', serif; font-size: 1.9rem; font-weight: 300; color: #1A1A2E; margin-bottom: .5rem; }
.dark .sec-title { color: #F5F0E8; }
.sec-sub { color: #777; font-size: .88rem; margin-bottom: 1.7rem; }
.dark .sec-sub { color: #AAAAC0; }
.card-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }
.card { background: #FFFFFF; border: 1px solid #E8E4DC; padding: 2rem; min-height: 185px; height: 100%; transition: all .2s ease; }
.card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(0,0,0,.08); }
.card-num { font-family: 'Noto Serif KR', serif; color: rgba(201,168,76,.45); font-size: 1.8rem; margin-bottom: .8rem; }
.card-title { color: #1A1A2E; font-weight: 600; font-size: 1.03rem; margin-bottom: .7rem; }
.card-desc { color: #666; font-size: .86rem; line-height: 1.75; }
.news-wrap { position: relative; }
.news-window { overflow: hidden; width: 100%; }
.news-track { display: flex; transition: transform .45s ease; }
.news-page { min-width: 100%; display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.2rem; }
.news-card { background: #fff; border: 1px solid #E8E4DC; overflow: hidden; min-height: 380px; }
.news-card img { width: 100%; height: 185px; object-fit: cover; filter: saturate(.9) contrast(.95); }
.news-card-body { padding: 1.4rem; }
.news-card-title { color: #1A1A2E; font-size: 1rem; font-weight: 600; margin-bottom: .65rem; }
.news-card-desc { color: #666; font-size: .84rem; line-height: 1.75; }
.news-arrow { position: absolute; top: 50%; transform: translateY(-50%); width: 42px; height: 42px; border-radius: 50%; border: 1px solid #C9A84C; background: rgba(10,10,22,.88); color: #C9A84C; font-size: 1.2rem; cursor: pointer; z-index: 2; }
.news-arrow:hover { background: #C9A84C; color: #1A1A2E; }
.news-arrow.left { left: -22px; }
.news-arrow.right { right: -22px; }
.news-dots { display: flex; justify-content: center; margin-top: 1.2rem; gap: .45rem; }
.news-dot { width: 28px; height: 3px; background: #CFC8B8; }
.news-dot.active { background: #C9A84C; }
.workflow-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: .8rem; }
.workflow-step { border: 1px solid rgba(201,168,76,.26); background: rgba(255,255,255,.04); padding: 1.4rem 1rem; min-height: 120px; }
.workflow-step-num { color: #C9A84C; font-family: 'Noto Serif KR', serif; font-size: 1.4rem; margin-bottom: .6rem; }
.workflow-step-title { color: #F5F0E8; font-size: .9rem; }
.footer { background: #0A0A16; border-top: 1px solid rgba(201,168,76,.18); padding: 2.5rem 5rem; color: #7777A0; font-size: .75rem; }
@media (max-width: 900px) { .patent-nav { overflow-x: auto; } .nav-links { justify-content: flex-start; } .card-grid, .stat-grid, .news-page, .workflow-grid { grid-template-columns: 1fr; } .hero-title { font-size: 2.2rem; } .section { padding: 3rem 1.5rem; } }
'''

def render_home_html():
    nav = build_nav_html()
    hero_imgs = [
        # 광화문 / 경복궁 계열 고화질 이미지
        "https://commons.wikimedia.org/wiki/Special:FilePath/Gwanghwamun%20Plaza%20-%20Gwanghwamun%20Gate%20back%20-%20Gyeongbokgung%20Palace%202016.jpg",
        # 제2롯데월드타워 고화질 이미지
        "https://commons.wikimedia.org/wiki/Special:FilePath/Lotte%20World%20Tower%20%2822074455581%29.jpg",
        # 남산타워 고화질 이미지
        "https://commons.wikimedia.org/wiki/Special:FilePath/N%20Seoul%20Tower%20%2813952097192%29.jpg",
    ]
    html = f'''
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{HOME_CSS}</style></head>
<body>
{nav}
<div class="hero">
    <div class="slide active" style="background-image:url('{hero_imgs[0]}')"></div>
    <div class="slide" style="background-image:url('{hero_imgs[1]}')"></div>
    <div class="slide" style="background-image:url('{hero_imgs[2]}')"></div>
    <div class="hero-content">
        <div class="hero-tag">{tr("hero_tag")}</div>
        <div class="hero-title">{tr("hero_title")}</div>
        <div class="hero-line"></div>
        <div class="hero-sub">{tr("hero_sub")}</div>
        <a class="hero-cta" href="?page=request&lang={lang}" target="_top">{tr("cta")} →</a>
    </div>
    <div class="hero-dots"><div class="hero-dot active"></div><div class="hero-dot"></div><div class="hero-dot"></div></div>
</div>
<div class="stat-grid">
    <div class="stat-box"><div class="stat-num">1,240+</div><div class="stat-label">{tr("stats_1")}</div></div>
    <div class="stat-box"><div class="stat-num">98.2%</div><div class="stat-label">{tr("stats_2")}</div></div>
    <div class="stat-box"><div class="stat-num">12</div><div class="stat-label">{tr("stats_3")}</div></div>
    <div class="stat-box"><div class="stat-num">542+</div><div class="stat-label">{tr("stats_4")}</div></div>
</div>
<div class="section">
    <div class="sec-line"></div>
    <div class="sec-title">{tr("services_title")}</div>
    <div class="sec-sub">{tr("services_sub")}</div>
    <div class="card-grid">
        <a href="?page=prior_art&lang={lang}" target="_top"><div class="card"><div class="card-num">01</div><div class="card-title">{tr("service_1_title")}</div><div class="card-desc">{tr("service_1_desc")}</div></div></a>
        <a href="?page=specification&lang={lang}" target="_top"><div class="card"><div class="card-num">02</div><div class="card-title">{tr("service_2_title")}</div><div class="card-desc">{tr("service_2_desc")}</div></div></a>
        <a href="?page=drawing&lang={lang}" target="_top"><div class="card"><div class="card-num">03</div><div class="card-title">{tr("service_3_title")}</div><div class="card-desc">{tr("service_3_desc")}</div></div></a>
    </div>
</div>
<div class="section alt">
    <div class="sec-line"></div>
    <div class="sec-title">{tr("news_title")}</div>
    <div class="sec-sub">{tr("news_sub")}</div>
    <div class="news-wrap">
        <button class="news-arrow left" onclick="moveNews(-1)">‹</button>
        <button class="news-arrow right" onclick="moveNews(1)">›</button>
        <div class="news-window">
            <div class="news-track" id="newsTrack">
                <div class="news-page">
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?artificial,intelligence,technology"><div class="news-card-body"><div class="news-card-title">{tr("news_1_title")}</div><div class="news-card-desc">{tr("news_1_desc")}</div></div></div>
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?patent,documents,law"><div class="news-card-body"><div class="news-card-title">{tr("news_2_title")}</div><div class="news-card-desc">{tr("news_2_desc")}</div></div></div>
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?diagram,engineering,blueprint"><div class="news-card-body"><div class="news-card-title">{tr("news_3_title")}</div><div class="news-card-desc">{tr("news_3_desc")}</div></div></div>
                </div>
                <div class="news-page">
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?legal,office,documents"><div class="news-card-body"><div class="news-card-title">{tr("news_4_title")}</div><div class="news-card-desc">{tr("news_4_desc")}</div></div></div>
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?analysis,data,screen"><div class="news-card-body"><div class="news-card-title">{tr("news_5_title")}</div><div class="news-card-desc">{tr("news_5_desc")}</div></div></div>
                    <div class="news-card"><img src="https://source.unsplash.com/1200x800/?classification,network,technology"><div class="news-card-body"><div class="news-card-title">{tr("news_6_title")}</div><div class="news-card-desc">{tr("news_6_desc")}</div></div></div>
                </div>
            </div>
        </div>
        <div class="news-dots"><div class="news-dot active"></div><div class="news-dot"></div></div>
    </div>
</div>
<div class="section dark">
    <div class="sec-line"></div><div class="sec-title">{tr("workflow_title")}</div><div class="sec-sub">{tr("workflow_sub")}</div>
    <div class="workflow-grid">
        <div class="workflow-step"><div class="workflow-step-num">01</div><div class="workflow-step-title">{tr("workflow_1")}</div></div>
        <div class="workflow-step"><div class="workflow-step-num">02</div><div class="workflow-step-title">{tr("workflow_2")}</div></div>
        <div class="workflow-step"><div class="workflow-step-num">03</div><div class="workflow-step-title">{tr("workflow_3")}</div></div>
        <div class="workflow-step"><div class="workflow-step-num">04</div><div class="workflow-step-title">{tr("workflow_4")}</div></div>
        <div class="workflow-step"><div class="workflow-step-num">05</div><div class="workflow-step-title">{tr("workflow_5")}</div></div>
    </div>
</div>
<div class="footer">
    <div style="font-family:'Noto Serif KR',serif;font-size:1rem;color:#F0EDE6;letter-spacing:.18em;">PATENT<span style="color:#C9A84C;">AI</span></div>
    <div style="margin-top:.6rem;line-height:1.8;">{tr("site_sub")} · OpenAI · Python · Streamlit · Patent Drawing Agent<br>© 2026 PatentAI. All rights reserved.</div>
</div>
<script>
let heroIndex = 0;
const slides = document.querySelectorAll('.slide');
const heroDots = document.querySelectorAll('.hero-dot');
slides.forEach(function(slide) {{
    const bg = slide.style.backgroundImage
        .replace('url("', '')
        .replace('")', '')
        .replace("url('", "")
        .replace("')", "");
    if (bg) {{
        const img = new Image();
        img.src = bg;
    }}
}});
function showHero(i) {{
    slides.forEach((s, idx) => s.classList.toggle('active', idx === i));
    heroDots.forEach((d, idx) => d.classList.toggle('active', idx === i));
    heroIndex = i;
}}
setInterval(function() {{
    heroIndex = (heroIndex + 1) % slides.length;
    showHero(heroIndex);
}}, 5000);
let newsIndex = 0;
const newsTrack = document.getElementById('newsTrack');
const newsDots = document.querySelectorAll('.news-dot');
function showNews(i) {{
    if (i < 0) i = 1;
    if (i > 1) i = 0;
    newsIndex = i;
    newsTrack.style.transform = `translateX(-${{newsIndex * 100}}%)`;
    newsDots.forEach((d, idx) => d.classList.toggle('active', idx === newsIndex));
}}
function moveNews(delta) {{ showNews(newsIndex + delta); }}
</script>
</body></html>
'''
    components.html(html, height=2080, scrolling=False)

def render_simple_nav():
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head><body>{build_nav_html()}</body></html>'
    components.html(html, height=260, scrolling=False)

def render_page_header(title, sub=""):
    st.markdown(f'<div style="background:#1A1A2E;padding:3rem 5rem;border-bottom:2px solid #C9A84C;"><div style="color:#C9A84C;font-size:.68rem;letter-spacing:.28em;text-transform:uppercase;margin-bottom:.7rem;">PATENTAI</div><div style="font-family:serif;color:#F5F0E8;font-size:2rem;font-weight:300;">{title}</div><div style="color:#AAAAC0;font-size:.86rem;margin-top:.7rem;">{sub}</div></div>', unsafe_allow_html=True)

def render_footer():
    st.markdown(f'<div style="background:#0A0A16;border-top:1px solid rgba(201,168,76,.18);padding:2.5rem 5rem;color:#7777A0;font-size:.75rem;"><div style="font-family:serif;font-size:1rem;color:#F0EDE6;letter-spacing:.18em;">PATENT<span style="color:#C9A84C;">AI</span></div><div style="margin-top:.6rem;line-height:1.8;">{tr("site_sub")} · OpenAI · Python · Streamlit · Patent Drawing Agent<br>© 2026 PatentAI. All rights reserved.</div></div>', unsafe_allow_html=True)

def page_ready(title_key):
    render_simple_nav()
    render_page_header(escape(tr(title_key)))
    st.markdown(f'<div style="background:#F5F4F1;padding:4rem 5rem;"><div style="width:38px;height:2px;background:#C9A84C;margin-bottom:1rem;"></div><div style="font-family:serif;font-size:1.9rem;color:#1A1A2E;margin-bottom:.5rem;">{escape(tr("ready_title"))}</div><div style="color:#777;font-size:.9rem;">{escape(tr("ready_body"))}</div></div>', unsafe_allow_html=True)
    render_footer()

def page_request():
    render_simple_nav()
    render_page_header(escape(tr("request_title")))
    st.markdown('<div style="background:#F5F4F1;padding:4rem 5rem;">', unsafe_allow_html=True)
    st.info("✓ " + tr("request_check"))
    with st.form("request_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input(tr("form_name"))
        phone = c2.text_input(tr("form_phone"))
        email = st.text_input(tr("form_email"))
        st.selectbox(tr("form_field"), T[lang]["fields"])
        subject = st.text_input(tr("form_subject"))
        content = st.text_area(tr("form_content"), height=180)
        submitted = st.form_submit_button(tr("form_submit"))
        if submitted:
            if name and phone and email and subject and content:
                st.success(tr("form_success"))
            else:
                st.error(tr("form_error"))
    st.markdown('</div>', unsafe_allow_html=True)
    render_footer()

def page_login(staff=False):
    render_simple_nav()
    title = tr("login_staff") if staff else tr("login_member")
    render_page_header(escape(title))
    st.markdown('<div style="background:#F5F4F1;padding:4rem 5rem;"><div style="max-width:420px;margin:0 auto;">', unsafe_allow_html=True)
    st.text_input(tr("login_id"))
    st.text_input(tr("login_pw"), type="password")
    if st.button(tr("login_btn"), use_container_width=True):
        st.warning(tr("login_ready"))
    st.markdown(f'<div style="margin-top:1rem;font-size:.85rem;color:#777;">{tr("login_no_account")} <a href="?page=request&lang={lang}">{tr("login_request")}</a></div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    render_footer()

def read_uploaded_text(uploaded_file):
    raw = uploaded_file.read()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")

def try_generate_drawings(drawing_agent, patent_text, app_num, export_svg, export_png, vision_review, auto_repair, repair_rounds):
    if not hasattr(drawing_agent, "generate_all_drawings"):
        raise AttributeError("drawing_agent.py 안에 generate_all_drawings 함수가 없습니다.")
    style_template = getattr(drawing_agent, "DEFAULT_STYLE_TEMPLATE", "patent_office")
    attempts = [
        lambda: drawing_agent.generate_all_drawings(invention_text=patent_text, app_num=app_num, output_dir="drawing_analysis", export_svg=export_svg, export_png=export_png, vision_review=vision_review, auto_repair=auto_repair, max_repair_rounds=repair_rounds, style_template=style_template),
        lambda: drawing_agent.generate_all_drawings(patent_text, app_num, "drawing_analysis", export_svg=export_svg, export_png=export_png, vision_review=vision_review, auto_repair=auto_repair, max_repair_rounds=repair_rounds, style_template=style_template),
        lambda: drawing_agent.generate_all_drawings(patent_text, app_num, "drawing_analysis"),
    ]
    last_error = None
    for fn in attempts:
        try:
            return fn()
        except TypeError as e:
            last_error = e
    raise last_error

def generic_agent_page(title_key, sub_key, module_name=None, function_names=None):
    render_simple_nav()
    render_page_header(escape(tr(title_key)), escape(tr(sub_key)))
    st.markdown('<div style="background:#F5F4F1;padding:4rem 5rem;">', unsafe_allow_html=True)
    user_text = st.text_area(tr("agent_input"), height=220)
    if st.button(tr("agent_run"), use_container_width=True):
        if not module_name:
            st.warning(tr("agent_missing"))
        else:
            try:
                mod = importlib.import_module(module_name)
                fn = None
                for name in (function_names or []):
                    if hasattr(mod, name):
                        fn = getattr(mod, name)
                        break
                if fn is None:
                    st.warning(tr("agent_missing"))
                else:
                    result = fn(user_text)
                    st.markdown(f"### {tr('agent_result')}")
                    st.write(result)
            except Exception as e:
                st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)
    render_footer()


def page_team():
    render_simple_nav()
    render_page_header("구성원 소개", "PatentAI 프로젝트를 함께 개발하는 6명의 팀원을 소개합니다.")

    st.markdown("""
    <div style="background:#F5F4F1;padding:4rem 5rem;">
        <div style="width:38px;height:2px;background:#C9A84C;margin-bottom:1rem;"></div>
        <div style="font-family:serif;font-size:1.9rem;color:#1A1A2E;margin-bottom:.5rem;">Our Team</div>
        <div style="color:#777;font-size:.9rem;margin-bottom:2rem;">
            특허 상담, 선행기술 조사, 명세서 작성, 도면 생성, UI/UX, 데이터 파이프라인을 함께 구축합니다.
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.3rem;margin-bottom:1.3rem;">
            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">01</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">김서현</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Frontend / PatentAI UI</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">홈페이지 UI, 다국어 전환, Streamlit 화면 구성, 도면 에이전트 연동을 담당합니다.</div>
            </div>

            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">02</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">팀원 2</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Prior Art Agent</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">선행기술 조사, 특허 데이터 검색, 유사도 분석 기능을 담당합니다.</div>
            </div>

            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">03</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">팀원 3</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Consultation Agent</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">발명 상담 흐름, 상담 로그 구조화, 발명 요약 기능을 담당합니다.</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.3rem;">
            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">04</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">팀원 4</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Specification Agent</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">청구항, 명세서 초안, 발명의 효과 및 구성요소 정리 기능을 담당합니다.</div>
            </div>

            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">05</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">팀원 5</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Drawing Agent</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">특허 도면 자동 생성, Mermaid 변환, SVG/PNG 렌더링 기능을 담당합니다.</div>
            </div>

            <div style="background:white;border:1px solid #E8E4DC;padding:2rem;min-height:285px;box-shadow:0 12px 30px rgba(0,0,0,.04);">
                <div style="width:108px;height:108px;border-radius:50%;background:linear-gradient(135deg,#1A1A2E,#C9A84C);margin-bottom:1rem;display:flex;align-items:center;justify-content:center;color:white;font-size:2rem;font-family:serif;">06</div>
                <div style="font-size:1.1rem;font-weight:600;color:#1A1A2E;">팀원 6</div>
                <div style="font-size:.82rem;color:#C9A84C;margin:.4rem 0;">Review / Integration</div>
                <div style="font-size:.85rem;color:#666;line-height:1.7;">검토 에이전트, 전체 서비스 통합, 테스트 및 발표 자료 정리를 담당합니다.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_footer()


def page_drawing():
    render_simple_nav()
    render_page_header(escape(tr("drawing_title")), escape(tr("drawing_sub")))
    st.markdown('<div style="background:#F5F4F1;padding:4rem 5rem;">', unsafe_allow_html=True)
    uploaded = st.file_uploader(tr("drawing_upload"), type=["txt"])
    pasted = st.text_area(tr("drawing_text"), height=240)
    app_num = st.text_input(tr("drawing_app_num"), value="WEB-TEST-001")
    with st.expander(tr("drawing_options"), expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        export_svg = c1.checkbox(tr("drawing_svg"), value=True)
        export_png = c2.checkbox(tr("drawing_png"), value=True)
        vision_review = c3.checkbox(tr("drawing_vision"), value=False)
        auto_repair = c4.checkbox(tr("drawing_repair"), value=True)
        repair_rounds = st.slider(tr("drawing_rounds"), 0, 3, 1)
    if st.button(tr("drawing_run"), use_container_width=True):
        if not uploaded and not pasted.strip():
            st.error(tr("drawing_no_input"))
            st.stop()
        patent_text = read_uploaded_text(uploaded) if uploaded else pasted
        if uploaded and not app_num.strip():
            app_num = Path(uploaded.name).stem
        with st.spinner(tr("drawing_running")):
            try:
                import drawing_agent
                results = try_generate_drawings(drawing_agent, patent_text, app_num.strip() or "WEB-TEST-001", export_svg, export_png, vision_review, auto_repair, repair_rounds)
                st.session_state["drawing_results"] = results
                st.success(tr("drawing_done"))
            except Exception as e:
                st.error(f'{tr("drawing_error")} {e}')
    results = st.session_state.get("drawing_results", [])
    if results:
        st.markdown(f"### {tr('drawing_result')}")
        for i, r in enumerate(results, 1):
            with st.container(border=True):
                fig_number = getattr(r, "fig_number", f"도 {i}")
                title = getattr(r, "diagram_title", "")
                score = getattr(r, "quality_score", "")
                grade = getattr(r, "quality_grade", "")
                st.markdown(f"#### {escape(str(fig_number))} {escape(str(title))}")
                m1, m2, m3 = st.columns(3)
                m1.metric("Score", score)
                m2.metric("Grade", grade)
                m3.write(getattr(r, "diagram_type", ""))
                svg_path = getattr(r, "svg_path", "")
                png_path = getattr(r, "png_path", "")
                json_path = getattr(r, "fig_json_path", "")
                if png_path and Path(png_path).exists():
                    st.image(png_path, use_container_width=True)
                elif svg_path and Path(svg_path).exists():
                    st.image(svg_path, use_container_width=True)
                d1, d2, d3 = st.columns(3)
                if svg_path and Path(svg_path).exists():
                    d1.download_button(tr("download") + " SVG", data=Path(svg_path).read_bytes(), file_name=Path(svg_path).name, mime="image/svg+xml", key=f"svg_{i}")
                if png_path and Path(png_path).exists():
                    d2.download_button(tr("download") + " PNG", data=Path(png_path).read_bytes(), file_name=Path(png_path).name, mime="image/png", key=f"png_{i}")
                if json_path and Path(json_path).exists():
                    d3.download_button(tr("download") + " JSON", data=Path(json_path).read_bytes(), file_name=Path(json_path).name, mime="application/json", key=f"json_{i}")
    st.markdown('</div>', unsafe_allow_html=True)
    render_footer()

def chatbot_answer(q):
    ql = q.lower()
    if any(k in ql for k in ["선행", "prior", "先行"]):
        return "prior_art", tr("chatbot_prior")
    if any(k in ql for k in ["명세", "spec", "说明", "明細"]):
        return "specification", tr("chatbot_spec")
    if any(k in ql for k in ["도면", "drawing", "附图", "図面"]):
        return "drawing", tr("chatbot_drawing")
    if any(k in ql for k in ["검토", "review", "审查", "審査"]):
        return "review", tr("chatbot_review")
    if any(k in ql for k in ["상담", "request", "consult", "咨询", "相談"]):
        return "request", tr("chatbot_request")
    return page, tr("chatbot_default")

def render_chatbot():
    if st.session_state.chat_is_open:
        st.markdown(f'<div class="chat-panel"><div class="chat-head"><span>{escape(tr("chatbot_title"))}</span><span>AI</span></div><div class="chat-body">', unsafe_allow_html=True)
        if not st.session_state.chat_msgs:
            st.markdown(f'<div class="chat-msg chat-bot">{escape(tr("chatbot_welcome"))}</div>', unsafe_allow_html=True)
        for role, msg in st.session_state.chat_msgs[-8:]:
            cls = "chat-user" if role == "user" else "chat-bot"
            st.markdown(f'<div class="chat-msg {cls}">{msg}</div>', unsafe_allow_html=True)
        st.markdown('</div></div>', unsafe_allow_html=True)
        user_msg = st.chat_input(tr("chatbot_ph"))
        if user_msg:
            target_page, ans = chatbot_answer(user_msg)
            answer_html = f'{escape(ans)} <a href="?page={target_page}&lang={lang}">→</a>'
            st.session_state.chat_msgs.append(("user", escape(user_msg)))
            st.session_state.chat_msgs.append(("bot", answer_html))
            st.rerun()
        st.markdown('<div class="chat-float">', unsafe_allow_html=True)
        if st.button("×", key="close_chat_btn"):
            st.session_state.chat_is_open = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="chat-float">', unsafe_allow_html=True)
        if st.button("💬", key="open_chat_btn"):
            st.session_state.chat_is_open = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if page == "home":
    render_home_html()
elif page == "drawing":
    page_drawing()
elif page == "request":
    page_request()
elif page == "member_login":
    page_login(staff=False)
elif page == "staff_login":
    page_login(staff=True)
elif page == "consultation":
    generic_agent_page("consultation_title", "consultation_sub", "consultation_agent", ["run", "main", "consult", "process"])
elif page == "prior_art":
    generic_agent_page("prior_title", "prior_sub", "prior_art_search", ["run", "main", "search", "process"])
elif page == "specification":
    generic_agent_page("spec_title", "spec_sub", "claim_to_flowchart", ["run", "main", "process"])
elif page == "review":
    generic_agent_page("review_title", "review_sub", None, None)
elif page == "about":
    page_ready("nav_about")
elif page == "team":
    page_team()
elif page == "news":
    page_ready("nav_news")
else:
    render_home_html()

render_chatbot()
