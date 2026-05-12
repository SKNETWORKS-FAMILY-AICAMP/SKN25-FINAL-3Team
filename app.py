# app.py - PatentAI 단일 파일 완성 버전
import os
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="PatentAI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LANGUAGES = {
    "ko": "한국어",
    "en": "English",
    "zh": "中文",
    "ja": "日本語",
}

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

T = {
    "ko": {
        "site_sub": "지식재산 상담 시스템",
        "login_member": "회원 로그인",
        "login_staff": "직원 로그인",
        "nav_home": "홈",
        "nav_about": "서비스 소개",
        "nav_about_intro": "PatentAI 소개",
        "nav_about_guide": "이용 안내",
        "nav_about_pricing": "요금제",
        "nav_about_faq": "자주 묻는 질문",
        "nav_consultation": "특허 상담",
        "nav_consult_invention": "발명 내용 상담",
        "nav_consult_strategy": "출원 전략 수립",
        "nav_consult_history": "상담 이력 조회",
        "nav_prior_art": "선행기술 조사",
        "nav_prior_auto": "자동 선행기술 검색",
        "nav_prior_similar": "유사 특허 분석",
        "nav_prior_report": "리스크 리포트",
        "nav_specification": "명세서 작성",
        "nav_claims": "청구항 자동 생성",
        "nav_drawing": "도면 자동 작성",
        "nav_spec_draft": "명세서 초안 생성",
        "nav_drawing_agent": "도면 에이전트",
        "nav_drawing_create": "도면 생성",
        "nav_drawing_batch": "배치 처리",
        "nav_drawing_history": "도면 이력",
        "nav_review": "검토 에이전트",
        "nav_review_novelty": "신규성 검토",
        "nav_review_inventive": "진보성 검토",
        "nav_review_clarity": "기재불비 검토",
        "nav_review_examiner": "심사관 관점 분석",
        "nav_request": "상담 신청",
        "nav_request_online": "온라인 상담 신청",
        "nav_request_visit": "방문 상담 예약",
        "nav_request_history": "상담 이력 조회",
        "nav_team": "구성원",
        "nav_team_intro": "팀 소개",
        "nav_team_expertise": "전문 분야",
        "nav_team_awards": "수상 및 실적",
        "nav_news": "소식/자료",
        "nav_news_patent": "최신 특허 뉴스",
        "nav_news_cases": "판례 분석",
        "nav_news_seminar": "세미나 자료",
        "hero_tag": "AI-Powered Patent Consultation System",
        "hero_title": "발명의 가치를<br><strong>권리로 만들어 드립니다</strong>",
        "hero_sub": "발명 내용을 자유롭게 설명해 주시면<br>AI가 특허 출원에 필요한 정보를 체계적으로 구조화해 드립니다",
        "cta": "상담 신청하기",
        "stats_1": "처리 특허 건수",
        "stats_2": "고객 만족도",
        "stats_3": "AI 전문 모델",
        "stats_4": "학습 특허 데이터",
        "services_title": "주요 서비스",
        "services_sub": "AI 기반 특허 출원 전 과정을 지원합니다",
        "service_1_title": "선행기술 조사",
        "service_1_desc": "발명 내용을 기반으로 유사 특허와 선행기술을 자동으로 탐색합니다.",
        "service_2_title": "명세서 작성",
        "service_2_desc": "청구항, 발명의 설명, 도면 설명을 구조화하여 초안을 생성합니다.",
        "service_3_title": "도면 에이전트",
        "service_3_desc": "특허 명세서를 분석하여 블록도와 흐름도를 자동 생성합니다.",
        "news_title": "최신 특허 동향",
        "news_sub": "국내외 주요 특허 뉴스와 판례를 정리해드립니다",
        "team_title": "구성원 소개",
        "request_title": "상담 신청",
        "request_check": "AI 전문가가 직접 상담을 진행합니다",
        "form_name": "성함",
        "form_phone": "연락처",
        "form_email": "이메일",
        "form_field": "기술 분야",
        "form_subject": "제목",
        "form_content": "발명 내용",
        "form_submit": "상담 신청하기",
        "form_success": "상담 신청이 완료되었습니다. 24시간 내 연락드리겠습니다.",
        "form_error": "필수 항목을 모두 입력해주세요.",
        "fields": ["AI/머신러닝", "반도체", "소프트웨어", "바이오/의료", "IoT/전자", "기계/화학", "기타"],
        "login_id": "아이디 / 이메일",
        "login_pw": "비밀번호",
        "login_btn": "로그인",
        "login_ready": "로그인 기능은 준비 중입니다.",
        "login_no_account": "계정이 없으신가요?",
        "login_request": "상담 신청하기",
        "chatbot_title": "PatentAI 상담봇",
        "chatbot_welcome": "안녕하세요! 궁금하신 점을 알려주세요 😊",
        "chatbot_ph": "궁금한 점을 입력하세요...",
        "chatbot_default": "더 구체적으로 말씀해 주시겠어요? 예: 선행기술, 명세서, 도면, 상담 신청",
        "chatbot_prior": "선행기술 조사 페이지로 안내해드릴게요.",
        "chatbot_spec": "명세서 작성 페이지로 안내해드릴게요.",
        "chatbot_drawing": "도면 생성 에이전트로 안내해드릴게요.",
        "chatbot_review": "검토 에이전트 페이지로 안내해드릴게요.",
        "chatbot_request": "상담 신청 페이지로 안내해드릴게요.",
        "drawing_title": "특허 도면 생성 에이전트",
        "drawing_sub": "특허 명세서를 업로드하면 자동으로 도면을 생성합니다",
        "drawing_upload": "특허 TXT 파일 업로드",
        "drawing_text": "또는 명세서 직접 입력",
        "drawing_app_num": "출원번호 / 작업 ID",
        "drawing_options": "생성 옵션",
        "drawing_svg": "SVG 생성",
        "drawing_png": "PNG 생성",
        "drawing_vision": "Vision 검수",
        "drawing_repair": "품질 미달 자동 보정",
        "drawing_rounds": "자동 보정 횟수",
        "drawing_run": "도면 생성 시작",
        "drawing_no_input": "파일을 업로드하거나 명세서 내용을 입력해주세요.",
        "drawing_running": "도면 생성 중입니다.",
        "drawing_done": "도면 생성 완료",
        "drawing_error": "도면 생성 중 오류가 발생했습니다.",
        "drawing_result": "생성 결과",
        "download": "다운로드",
        "ready_title": "페이지 준비 중",
        "ready_body": "이 영역은 동일한 네비게이션, 챗봇, 다국어 구조로 확장할 수 있습니다.",
    },
    "en": {
        "site_sub": "IP Consultation System",
        "login_member": "Member Login",
        "login_staff": "Staff Login",
        "nav_home": "Home",
        "nav_about": "About",
        "nav_about_intro": "About PatentAI",
        "nav_about_guide": "How to Use",
        "nav_about_pricing": "Pricing",
        "nav_about_faq": "FAQ",
        "nav_consultation": "Consultation",
        "nav_consult_invention": "Invention Consultation",
        "nav_consult_strategy": "Filing Strategy",
        "nav_consult_history": "Consultation History",
        "nav_prior_art": "Prior Art",
        "nav_prior_auto": "Auto Prior Art Search",
        "nav_prior_similar": "Similar Patent Analysis",
        "nav_prior_report": "Risk Report",
        "nav_specification": "Specification",
        "nav_claims": "Auto Claim Generation",
        "nav_drawing": "Auto Drawing Creation",
        "nav_spec_draft": "Draft Specification",
        "nav_drawing_agent": "Drawing Agent",
        "nav_drawing_create": "Create Drawings",
        "nav_drawing_batch": "Batch Processing",
        "nav_drawing_history": "Drawing History",
        "nav_review": "Review Agent",
        "nav_review_novelty": "Novelty Review",
        "nav_review_inventive": "Inventive Step Review",
        "nav_review_clarity": "Clarity Review",
        "nav_review_examiner": "Examiner Perspective",
        "nav_request": "Request",
        "nav_request_online": "Online Consultation",
        "nav_request_visit": "Visit Reservation",
        "nav_request_history": "Request History",
        "nav_team": "Team",
        "nav_team_intro": "Team Introduction",
        "nav_team_expertise": "Expertise",
        "nav_team_awards": "Awards",
        "nav_news": "News",
        "nav_news_patent": "Patent News",
        "nav_news_cases": "Case Analysis",
        "nav_news_seminar": "Seminar Materials",
        "hero_tag": "AI-Powered Patent Consultation System",
        "hero_title": "Turning Your Invention<br><strong>Into Protected Rights</strong>",
        "hero_sub": "Describe your invention freely<br>and AI will structure the information required for patent filing",
        "cta": "Get Consultation",
        "stats_1": "Patents Processed",
        "stats_2": "Client Satisfaction",
        "stats_3": "AI Models",
        "stats_4": "Training Patents",
        "services_title": "Main Services",
        "services_sub": "AI-powered support for the entire patent filing process",
        "service_1_title": "Prior Art Search",
        "service_1_desc": "Automatically search similar patents and prior art based on invention details.",
        "service_2_title": "Specification Drafting",
        "service_2_desc": "Generate structured drafts for claims, description, and drawing explanations.",
        "service_3_title": "Drawing Agent",
        "service_3_desc": "Analyze patent specifications and generate block diagrams and flowcharts.",
        "news_title": "Latest Patent Trends",
        "news_sub": "Major patent news and cases from Korea and abroad",
        "team_title": "Our Team",
        "request_title": "Consultation Request",
        "request_check": "An AI specialist will directly support your consultation",
        "form_name": "Name",
        "form_phone": "Phone",
        "form_email": "Email",
        "form_field": "Technical Field",
        "form_subject": "Subject",
        "form_content": "Invention Description",
        "form_submit": "Submit Request",
        "form_success": "Request submitted. We will contact you within 24 hours.",
        "form_error": "Please fill in all required fields.",
        "fields": ["AI/Machine Learning", "Semiconductor", "Software", "Bio/Medical", "IoT/Electronics", "Mechanical/Chemical", "Other"],
        "login_id": "ID / Email",
        "login_pw": "Password",
        "login_btn": "Login",
        "login_ready": "Login feature is under preparation.",
        "login_no_account": "No account?",
        "login_request": "Request Consultation",
        "chatbot_title": "PatentAI Bot",
        "chatbot_welcome": "Hello! How can I help you? 😊",
        "chatbot_ph": "Ask me anything...",
        "chatbot_default": "Could you be more specific? e.g., prior art, specification, drawings, consultation",
        "chatbot_prior": "I will guide you to the Prior Art page.",
        "chatbot_spec": "I will guide you to the Specification page.",
        "chatbot_drawing": "I will guide you to the Drawing Agent.",
        "chatbot_review": "I will guide you to the Review Agent.",
        "chatbot_request": "I will guide you to the Consultation Request page.",
        "drawing_title": "Patent Drawing Agent",
        "drawing_sub": "Upload a patent specification to automatically generate drawings",
        "drawing_upload": "Upload patent TXT file",
        "drawing_text": "Or paste patent specification text",
        "drawing_app_num": "Application No. / Job ID",
        "drawing_options": "Generation Options",
        "drawing_svg": "Generate SVG",
        "drawing_png": "Generate PNG",
        "drawing_vision": "Vision Review",
        "drawing_repair": "Auto-repair low-quality drawings",
        "drawing_rounds": "Repair Rounds",
        "drawing_run": "Start Drawing Generation",
        "drawing_no_input": "Please upload a file or enter specification text.",
        "drawing_running": "Generating drawings.",
        "drawing_done": "Drawing generation complete",
        "drawing_error": "An error occurred while generating drawings.",
        "drawing_result": "Generated Results",
        "download": "Download",
        "ready_title": "Page in Progress",
        "ready_body": "This area can be expanded with the same navigation, chatbot, and multilingual structure.",
    },
    "zh": {
        "site_sub": "知识产权咨询系统",
        "login_member": "会员登录",
        "login_staff": "员工登录",
        "nav_home": "首页",
        "nav_about": "服务介绍",
        "nav_about_intro": "关于 PatentAI",
        "nav_about_guide": "使用说明",
        "nav_about_pricing": "收费标准",
        "nav_about_faq": "常见问题",
        "nav_consultation": "专利咨询",
        "nav_consult_invention": "发明内容咨询",
        "nav_consult_strategy": "申请策略制定",
        "nav_consult_history": "咨询记录",
        "nav_prior_art": "先行技术调查",
        "nav_prior_auto": "自动先行技术搜索",
        "nav_prior_similar": "类似专利分析",
        "nav_prior_report": "风险报告",
        "nav_specification": "说明书撰写",
        "nav_claims": "权利要求自动生成",
        "nav_drawing": "附图自动生成",
        "nav_spec_draft": "说明书草案生成",
        "nav_drawing_agent": "附图代理",
        "nav_drawing_create": "生成附图",
        "nav_drawing_batch": "批量处理",
        "nav_drawing_history": "附图记录",
        "nav_review": "审查代理",
        "nav_review_novelty": "新颖性审查",
        "nav_review_inventive": "创造性审查",
        "nav_review_clarity": "清晰性审查",
        "nav_review_examiner": "审查员视角分析",
        "nav_request": "咨询申请",
        "nav_request_online": "在线咨询申请",
        "nav_request_visit": "预约上门咨询",
        "nav_request_history": "咨询记录查询",
        "nav_team": "团队成员",
        "nav_team_intro": "团队介绍",
        "nav_team_expertise": "专业领域",
        "nav_team_awards": "奖项与业绩",
        "nav_news": "新闻资料",
        "nav_news_patent": "最新专利新闻",
        "nav_news_cases": "判例分析",
        "nav_news_seminar": "研讨会资料",
        "hero_tag": "AI驱动的专利咨询系统",
        "hero_title": "将您的发明<br><strong>转化为受保护的权利</strong>",
        "hero_sub": "自由描述您的发明内容<br>AI将系统化整理专利申请所需信息",
        "cta": "申请咨询",
        "stats_1": "处理专利件数",
        "stats_2": "客户满意度",
        "stats_3": "AI专业模型",
        "stats_4": "学习专利数据",
        "services_title": "主要服务",
        "services_sub": "AI驱动，支持专利申请全流程",
        "service_1_title": "先行技术调查",
        "service_1_desc": "根据发明内容自动搜索类似专利和先行技术。",
        "service_2_title": "说明书撰写",
        "service_2_desc": "生成权利要求、说明书和附图说明的结构化草案。",
        "service_3_title": "附图代理",
        "service_3_desc": "分析专利说明书并自动生成框图和流程图。",
        "news_title": "最新专利动态",
        "news_sub": "为您整理国内外主要专利新闻和判例",
        "team_title": "团队成员介绍",
        "request_title": "咨询申请",
        "request_check": "AI专家将直接协助咨询",
        "form_name": "姓名",
        "form_phone": "联系方式",
        "form_email": "电子邮件",
        "form_field": "技术领域",
        "form_subject": "标题",
        "form_content": "发明内容",
        "form_submit": "提交申请",
        "form_success": "申请已提交，我们将在24小时内与您联系。",
        "form_error": "请填写所有必填项。",
        "fields": ["AI/机器学习", "半导体", "软件", "生物/医疗", "IoT/电子", "机械/化学", "其他"],
        "login_id": "账号 / 邮箱",
        "login_pw": "密码",
        "login_btn": "登录",
        "login_ready": "功能准备中。",
        "login_no_account": "没有账号？",
        "login_request": "申请咨询",
        "chatbot_title": "PatentAI 咨询机器人",
        "chatbot_welcome": "您好！请告诉我您的问题 😊",
        "chatbot_ph": "请输入您的问题...",
        "chatbot_default": "请更具体说明，例如：先行技术、说明书、附图、咨询",
        "chatbot_prior": "为您引导至先行技术调查页面。",
        "chatbot_spec": "为您引导至说明书撰写页面。",
        "chatbot_drawing": "为您引导至附图代理页面。",
        "chatbot_review": "为您引导至审查代理页面。",
        "chatbot_request": "为您引导至咨询申请页面。",
        "drawing_title": "专利附图生成代理",
        "drawing_sub": "上传专利说明书后自动生成附图",
        "drawing_upload": "上传专利 TXT 文件",
        "drawing_text": "或直接输入专利说明书",
        "drawing_app_num": "申请号 / 任务 ID",
        "drawing_options": "生成选项",
        "drawing_svg": "生成 SVG",
        "drawing_png": "生成 PNG",
        "drawing_vision": "Vision 审查",
        "drawing_repair": "自动修复低质量附图",
        "drawing_rounds": "自动修复次数",
        "drawing_run": "开始生成附图",
        "drawing_no_input": "请上传文件或输入说明书内容。",
        "drawing_running": "正在生成附图。",
        "drawing_done": "附图生成完成",
        "drawing_error": "生成附图时发生错误。",
        "drawing_result": "生成结果",
        "download": "下载",
        "ready_title": "页面准备中",
        "ready_body": "该区域可用统一导航、聊天机器人和多语言结构继续扩展。",
    },
    "ja": {
        "site_sub": "知的財産相談システム",
        "login_member": "会員ログイン",
        "login_staff": "スタッフログイン",
        "nav_home": "ホーム",
        "nav_about": "サービス紹介",
        "nav_about_intro": "PatentAIについて",
        "nav_about_guide": "ご利用案内",
        "nav_about_pricing": "料金プラン",
        "nav_about_faq": "よくある質問",
        "nav_consultation": "特許相談",
        "nav_consult_invention": "発明内容相談",
        "nav_consult_strategy": "出願戦略策定",
        "nav_consult_history": "相談履歴照会",
        "nav_prior_art": "先行技術調査",
        "nav_prior_auto": "自動先行技術検索",
        "nav_prior_similar": "類似特許分析",
        "nav_prior_report": "リスクレポート",
        "nav_specification": "明細書作成",
        "nav_claims": "クレーム自動生成",
        "nav_drawing": "図面自動作成",
        "nav_spec_draft": "明細書草案生成",
        "nav_drawing_agent": "図面エージェント",
        "nav_drawing_create": "図面生成",
        "nav_drawing_batch": "バッチ処理",
        "nav_drawing_history": "図面履歴",
        "nav_review": "審査エージェント",
        "nav_review_novelty": "新規性審査",
        "nav_review_inventive": "進歩性審査",
        "nav_review_clarity": "記載不備審査",
        "nav_review_examiner": "審査官観点分析",
        "nav_request": "相談申請",
        "nav_request_online": "オンライン相談申請",
        "nav_request_visit": "来訪相談予約",
        "nav_request_history": "相談履歴照会",
        "nav_team": "メンバー",
        "nav_team_intro": "チーム紹介",
        "nav_team_expertise": "専門分野",
        "nav_team_awards": "受賞・実績",
        "nav_news": "ニュース",
        "nav_news_patent": "最新特許ニュース",
        "nav_news_cases": "判例分析",
        "nav_news_seminar": "セミナー資料",
        "hero_tag": "AI搭載特許相談システム",
        "hero_title": "あなたの発明を<br><strong>権利として守ります</strong>",
        "hero_sub": "発明内容を自由にご説明ください<br>AIが特許出願に必要な情報を体系的に整理いたします",
        "cta": "相談申請",
        "stats_1": "処理特許件数",
        "stats_2": "顧客満足度",
        "stats_3": "AI専門モデル",
        "stats_4": "学習特許データ",
        "services_title": "主要サービス",
        "services_sub": "AI搭載で特許出願の全工程をサポート",
        "service_1_title": "先行技術調査",
        "service_1_desc": "発明内容に基づき類似特許と先行技術を自動検索します。",
        "service_2_title": "明細書作成",
        "service_2_desc": "クレーム、発明の説明、図面説明を構造化して草案を生成します。",
        "service_3_title": "図面エージェント",
        "service_3_desc": "特許明細書を分析し、ブロック図とフローチャートを自動生成します。",
        "news_title": "最新特許動向",
        "news_sub": "国内外の主要特許ニュースと判例をまとめてお届けします",
        "team_title": "メンバー紹介",
        "request_title": "相談申請",
        "request_check": "AI専門家が直接相談を支援します",
        "form_name": "お名前",
        "form_phone": "電話番号",
        "form_email": "メール",
        "form_field": "技術分野",
        "form_subject": "件名",
        "form_content": "発明内容",
        "form_submit": "相談申請する",
        "form_success": "申請が完了しました。24時間以内にご連絡いたします。",
        "form_error": "必須項目をすべてご入力ください。",
        "fields": ["AI/機械学習", "半導体", "ソフトウェア", "バイオ/医療", "IoT/電子", "機械/化学", "その他"],
        "login_id": "ID / メール",
        "login_pw": "パスワード",
        "login_btn": "ログイン",
        "login_ready": "準備中です。",
        "login_no_account": "アカウントをお持ちでない方は",
        "login_request": "相談申請",
        "chatbot_title": "PatentAI相談ボット",
        "chatbot_welcome": "こんにちは！ご質問をお気軽にどうぞ 😊",
        "chatbot_ph": "ご質問を入力してください...",
        "chatbot_default": "もう少し具体的にお教えください。例：先行技術、明細書、図面、相談",
        "chatbot_prior": "先行技術調査ページへご案内します。",
        "chatbot_spec": "明細書作成ページへご案内します。",
        "chatbot_drawing": "図面エージェントへご案内します。",
        "chatbot_review": "審査エージェントページへご案内します。",
        "chatbot_request": "相談申請ページへご案内します。",
        "drawing_title": "特許図面生成エージェント",
        "drawing_sub": "特許明細書をアップロードすると自動で図面を生成します",
        "drawing_upload": "特許 TXT ファイルをアップロード",
        "drawing_text": "または特許明細書を直接入力",
        "drawing_app_num": "出願番号 / 作業 ID",
        "drawing_options": "生成オプション",
        "drawing_svg": "SVG生成",
        "drawing_png": "PNG生成",
        "drawing_vision": "Vision検査",
        "drawing_repair": "低品質図面の自動修正",
        "drawing_rounds": "自動修正回数",
        "drawing_run": "図面生成開始",
        "drawing_no_input": "ファイルをアップロードするか、明細書内容を入力してください。",
        "drawing_running": "図面を生成中です。",
        "drawing_done": "図面生成完了",
        "drawing_error": "図面生成中にエラーが発生しました。",
        "drawing_result": "生成結果",
        "download": "ダウンロード",
        "ready_title": "ページ準備中",
        "ready_body": "この領域は同じナビゲーション、チャットボット、多言語構造で拡張できます。",
    },
}


def get_query_value(key, default=None):
    try:
        value = st.query_params.get(key, default)
        if isinstance(value, list):
            return value[0] if value else default
        return value
    except Exception:
        return default


if "lang" not in st.session_state:
    st.session_state.lang = "ko"
if "page" not in st.session_state:
    st.session_state.page = "home"
if "chat_is_open" not in st.session_state:
    st.session_state.chat_is_open = False
if "chat_msgs" not in st.session_state:
    st.session_state.chat_msgs = []
if "sid" not in st.session_state:
    st.session_state.sid = str(uuid.uuid4())[:8]

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


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500&family=Noto+Sans+KR:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

html, body, .stApp {
    margin: 0 !important;
    padding: 0 !important;
    background: #0A0A16 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}

header[data-testid="stHeader"], section[data-testid="stSidebar"] {
    display: none !important;
}

.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

[data-testid="stVerticalBlock"] { gap: 0 !important; }
.element-container { margin: 0 !important; }
.main .block-container { padding-top: 0 !important; }

.patent-nav-wrap {
    width: 100%;
    background: #0A0A16;
    border-bottom: 1px solid rgba(201,168,76,.22);
    position: relative;
    z-index: 9999;
}

.patent-nav {
    width: 100%;
    height: 74px;
    background: #0A0A16;
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    padding: 0 2.4rem;
    position: relative;
    z-index: 9999;
}

.logo {
    font-family: 'Noto Serif KR', serif;
    font-size: 1.05rem;
    color: #F0EDE6 !important;
    letter-spacing: .20em;
    display: flex;
    align-items: center;
    text-decoration: none !important;
    white-space: nowrap;
}

.logo em { color: #C9A84C; font-style: normal; }

.logo span {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: .67rem;
    color: #7777A0;
    margin-left: .9rem;
    letter-spacing: .08em;
}

.nav-links {
    display: flex;
    align-items: stretch;
    justify-content: center;
    flex: 1;
    margin-left: 2rem;
}

.nav-item {
    position: relative;
    display: flex;
    align-items: center;
}

.nav-label {
    height: 74px;
    display: flex;
    align-items: center;
    padding: 0 .85rem;
    font-size: .74rem;
    color: #C8C8D8 !important;
    letter-spacing: .04em;
    text-decoration: none !important;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    white-space: nowrap;
    transition: all .2s ease;
}

.nav-item:hover .nav-label {
    color: #C9A84C !important;
    border-bottom-color: #C9A84C;
}

.dropdown {
    display: none;
    position: absolute;
    top: 74px;
    left: 0;
    min-width: 205px;
    background: #0D0D1A;
    border: 1px solid rgba(201,168,76,.28);
    border-top: 2px solid #C9A84C;
    padding: .55rem 0;
    box-shadow: 0 20px 45px rgba(0,0,0,.55);
    z-index: 20000;
}

.nav-item:hover .dropdown { display: block; }

.dropdown a {
    display: block;
    padding: .58rem 1.2rem;
    font-size: .76rem;
    color: #AFAFC5 !important;
    text-decoration: none !important;
    border-left: 2px solid transparent;
    white-space: nowrap;
    transition: all .15s ease;
}

.dropdown a:hover {
    color: #C9A84C !important;
    background: rgba(201,168,76,.08);
    border-left-color: #C9A84C;
    padding-left: 1.55rem;
}

.nav-right {
    display: flex;
    align-items: center;
    gap: .55rem;
}

.lang-box { position: relative; }

.lang-btn {
    height: 34px;
    padding: 0 .8rem;
    border: 1px solid rgba(201,168,76,.38);
    color: #C8C8D8 !important;
    display: flex;
    align-items: center;
    gap: .35rem;
    font-size: .72rem;
    text-decoration: none !important;
    white-space: nowrap;
    cursor: pointer;
    background: transparent;
}

.lang-box:hover .lang-btn {
    color: #C9A84C !important;
    border-color: #C9A84C;
}

.lang-dropdown {
    display: none;
    position: absolute;
    top: 34px;
    right: 0;
    min-width: 145px;
    background: #0D0D1A;
    border: 1px solid rgba(201,168,76,.28);
    border-top: 2px solid #C9A84C;
    padding: .45rem 0;
    box-shadow: 0 18px 42px rgba(0,0,0,.55);
    z-index: 21000;
}

.lang-box:hover .lang-dropdown { display: block; }

.lang-dropdown a {
    display: block;
    padding: .58rem 1.1rem;
    font-size: .76rem;
    color: #AFAFC5 !important;
    text-decoration: none !important;
    white-space: nowrap;
    border-left: 2px solid transparent;
}

.lang-dropdown a:hover, .lang-dropdown a.active {
    color: #C9A84C !important;
    background: rgba(201,168,76,.08);
    border-left-color: #C9A84C;
}

.login-link {
    height: 34px;
    padding: 0 .85rem;
    border: 1px solid rgba(201,168,76,.38);
    color: #C8C8D8 !important;
    display: flex;
    align-items: center;
    font-size: .72rem;
    text-decoration: none !important;
    white-space: nowrap;
}

.login-link:hover {
    color: #C9A84C !important;
    border-color: #C9A84C;
}

.hero {
    position: relative;
    width: 100%;
    height: 620px;
    background-image:
        linear-gradient(180deg, rgba(8,8,18,.15), rgba(8,8,18,.88)),
        url('https://images.unsplash.com/photo-1532649097480-b67d52743b69?w=1920&q=95&fit=crop');
    background-size: cover;
    background-position: center;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin: 0 !important;
}

.hero-content {
    position: relative;
    z-index: 2;
    padding: 0 2rem;
}

.hero-tag {
    font-size: .68rem;
    letter-spacing: .38em;
    color: #C9A84C;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
}

.hero-title {
    font-family: 'Noto Serif KR', serif;
    font-size: 3rem;
    font-weight: 300;
    color: #F0EDE6;
    line-height: 1.55;
}

.hero-title strong {
    color: #F5F0E8;
    font-weight: 500;
}

.hero-line {
    width: 38px;
    height: 1px;
    background: #C9A84C;
    margin: 1.25rem auto;
}

.hero-sub {
    color: #D5D5DF;
    font-size: .95rem;
    line-height: 1.9;
}

.hero-cta {
    display: inline-block;
    margin-top: 1.8rem;
    padding: .8rem 2.4rem;
    border: 1px solid #C9A84C;
    color: #C9A84C !important;
    text-decoration: none !important;
    letter-spacing: .12em;
    font-size: .8rem;
    transition: all .2s ease;
}

.hero-cta:hover {
    background: #C9A84C;
    color: #1A1A2E !important;
}

.section {
    background: #F5F4F1;
    padding: 4rem 5rem;
}

.sec-line {
    width: 38px;
    height: 2px;
    background: #C9A84C;
    margin-bottom: 1rem;
}

.sec-title {
    font-family: 'Noto Serif KR', serif;
    font-size: 1.9rem;
    font-weight: 300;
    color: #1A1A2E;
    margin-bottom: .5rem;
}

.sec-sub {
    color: #777;
    font-size: .88rem;
    margin-bottom: 1.7rem;
}

.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
}

.stat-box {
    background: #111128;
    border-right: 1px solid rgba(201,168,76,.18);
    text-align: center;
    padding: 2rem 1rem;
}

.stat-num {
    font-family: 'Noto Serif KR', serif;
    color: #C9A84C;
    font-size: 2.5rem;
    font-weight: 300;
}

.stat-label {
    color: #B8B8C8;
    font-size: .75rem;
    letter-spacing: .1em;
    margin-top: .4rem;
}

.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.2rem;
}

.card {
    background: #FFFFFF;
    border: 1px solid #E8E4DC;
    padding: 2rem;
    min-height: 185px;
    transition: all .2s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(0,0,0,.08);
}

.card-num {
    font-family: 'Noto Serif KR', serif;
    color: rgba(201,168,76,.45);
    font-size: 1.8rem;
    margin-bottom: .8rem;
}

.card-title {
    color: #1A1A2E;
    font-weight: 600;
    font-size: 1.03rem;
    margin-bottom: .7rem;
}

.card-desc {
    color: #666;
    font-size: .86rem;
    line-height: 1.75;
}

.page-header {
    background: #1A1A2E;
    padding: 3rem 5rem;
    border-bottom: 2px solid #C9A84C;
}

.page-tag {
    color: #C9A84C;
    font-size: .68rem;
    letter-spacing: .28em;
    text-transform: uppercase;
    margin-bottom: .7rem;
}

.page-title {
    font-family: 'Noto Serif KR', serif;
    color: #F5F0E8;
    font-size: 2rem;
    font-weight: 300;
}

.page-sub {
    color: #AAAAC0;
    font-size: .86rem;
    margin-top: .7rem;
}

.footer {
    background: #0A0A16;
    border-top: 1px solid rgba(201,168,76,.18);
    padding: 2.5rem 5rem;
    color: #7777A0;
    font-size: .75rem;
}

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    border-radius: 2px !important;
}

.stButton > button {
    background: #1A1A2E !important;
    color: #F5F0E8 !important;
    border: none !important;
    border-radius: 2px !important;
    padding: .65rem 1.5rem !important;
}

.stButton > button:hover {
    background: #C9A84C !important;
    color: #1A1A2E !important;
}

.chat-float {
    position: fixed;
    right: 24px;
    bottom: 24px;
    z-index: 30000;
}

.chat-panel {
    position: fixed;
    right: 24px;
    bottom: 88px;
    width: 360px;
    background: #FFFFFF;
    border: 1px solid #E8E4DC;
    box-shadow: 0 18px 45px rgba(0,0,0,.22);
    z-index: 30000;
}

.chat-head {
    background: #1A1A2E;
    color: #F5F0E8;
    padding: .9rem 1rem;
    font-size: .86rem;
    display: flex;
    justify-content: space-between;
}

.chat-body {
    padding: 1rem;
    max-height: 280px;
    overflow-y: auto;
    font-size: .82rem;
}

.chat-msg {
    padding: .65rem .75rem;
    border-radius: 6px;
    margin-bottom: .65rem;
    line-height: 1.55;
}

.chat-bot {
    background: #F5F4F1;
    margin-right: 2rem;
}

.chat-user {
    background: #EFE8D1;
    margin-left: 2rem;
}

@media (max-width: 1200px) {
    .nav-label {
        padding: 0 .45rem;
        font-size: .68rem;
    }
    .logo span { display: none; }
    .card-grid, .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
""", unsafe_allow_html=True)


def render_nav():
    nav_html = ""
    for page_key, label_key, subs in NAV_ITEMS:
        sub_html = "".join([f'<a href="?page={page_key}&lang={lang}">{tr(sub_key)}</a>' for sub_key in subs])
        if subs:
            nav_html += f"""
            <div class="nav-item">
                <a class="nav-label" href="?page={page_key}&lang={lang}">{tr(label_key)}</a>
                <div class="dropdown">{sub_html}</div>
            </div>
            """
        else:
            nav_html += f"""
            <div class="nav-item">
                <a class="nav-label" href="?page={page_key}&lang={lang}">{tr(label_key)}</a>
            </div>
            """

    lang_html = ""
    for code, label in LANGUAGES.items():
        active = "active" if code == lang else ""
        lang_html += f'<a class="{active}" href="?page={page}&lang={code}">{label}</a>'

    st.markdown(f"""
    <div class="patent-nav-wrap">
        <div class="patent-nav">
            <a class="logo" href="?page=home&lang={lang}">
                PATENT<em>AI</em><span>{tr("site_sub")}</span>
            </a>
            <div class="nav-links">{nav_html}</div>
            <div class="nav-right">
                <div class="lang-box">
                    <div class="lang-btn">🌐 {LANGUAGES[lang]} ▾</div>
                    <div class="lang-dropdown">{lang_html}</div>
                </div>
                <a class="login-link" href="?page=member_login&lang={lang}">{tr("login_member")}</a>
                <a class="login-link" href="?page=staff_login&lang={lang}">{tr("login_staff")}</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title, sub=None):
    st.markdown(f"""
    <div class="page-header">
        <div class="page-tag">PATENTAI</div>
        <div class="page-title">{title}</div>
        <div class="page-sub">{sub or ""}</div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown(f"""
    <div class="footer">
        <div style="font-family:'Noto Serif KR',serif;font-size:1rem;color:#F0EDE6;letter-spacing:.18em;">
            PATENT<span style="color:#C9A84C;">AI</span>
        </div>
        <div style="margin-top:.6rem;line-height:1.8;">
            {tr("site_sub")} · OpenAI · Python · Streamlit · Patent Drawing Agent<br>
            © 2026 PatentAI. All rights reserved.
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_home():
    st.markdown(f"""
    <div class="hero">
        <div class="hero-content">
            <div class="hero-tag">{tr("hero_tag")}</div>
            <div class="hero-title">{tr("hero_title")}</div>
            <div class="hero-line"></div>
            <div class="hero-sub">{tr("hero_sub")}</div>
            <a class="hero-cta" href="?page=request&lang={lang}">{tr("cta")} →</a>
        </div>
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
            <a href="?page=prior_art&lang={lang}" style="text-decoration:none;">
                <div class="card">
                    <div class="card-num">01</div>
                    <div class="card-title">{tr("service_1_title")}</div>
                    <div class="card-desc">{tr("service_1_desc")}</div>
                </div>
            </a>
            <a href="?page=specification&lang={lang}" style="text-decoration:none;">
                <div class="card">
                    <div class="card-num">02</div>
                    <div class="card-title">{tr("service_2_title")}</div>
                    <div class="card-desc">{tr("service_2_desc")}</div>
                </div>
            </a>
            <a href="?page=drawing&lang={lang}" style="text-decoration:none;">
                <div class="card">
                    <div class="card-num">03</div>
                    <div class="card-title">{tr("service_3_title")}</div>
                    <div class="card-desc">{tr("service_3_desc")}</div>
                </div>
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_ready(title_key):
    render_page_header(tr(title_key))
    st.markdown(f"""
    <div class="section">
        <div class="sec-line"></div>
        <div class="sec-title">{tr("ready_title")}</div>
        <div class="sec-sub">{tr("ready_body")}</div>
    </div>
    """, unsafe_allow_html=True)


def page_request():
    render_page_header(tr("request_title"))
    st.markdown('<div class="section">', unsafe_allow_html=True)
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


def page_login(staff=False):
    title = tr("login_staff") if staff else tr("login_member")
    render_page_header(title)
    st.markdown('<div class="section"><div style="max-width:420px;margin:0 auto;">', unsafe_allow_html=True)
    st.text_input(tr("login_id"))
    st.text_input(tr("login_pw"), type="password")
    if st.button(tr("login_btn"), use_container_width=True):
        st.warning(tr("login_ready"))
    st.markdown(
        f'<div style="margin-top:1rem;font-size:.85rem;color:#777;">'
        f'{tr("login_no_account")} '
        f'<a href="?page=request&lang={lang}">{tr("login_request")}</a>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div></div>', unsafe_allow_html=True)


def read_uploaded_text(uploaded_file):
    raw = uploaded_file.read()
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr"]:
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", errors="ignore")


def page_drawing():
    render_page_header(tr("drawing_title"), tr("drawing_sub"))
    st.markdown('<div class="section">', unsafe_allow_html=True)

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

                try:
                    results = drawing_agent.generate_all_drawings(
                        invention_text=patent_text,
                        app_num=app_num.strip() or "WEB-TEST-001",
                        output_dir="drawing_analysis",
                        export_svg=export_svg,
                        export_png=export_png,
                        vision_review=vision_review,
                        auto_repair=auto_repair,
                        max_repair_rounds=repair_rounds,
                        style_template=getattr(drawing_agent, "DEFAULT_STYLE_TEMPLATE", "patent_office"),
                    )
                except TypeError:
                    results = drawing_agent.generate_all_drawings(
                        patent_text,
                        app_num.strip() or "WEB-TEST-001",
                        "drawing_analysis",
                        export_svg=export_svg,
                        export_png=export_png,
                        vision_review=vision_review,
                        auto_repair=auto_repair,
                        style_template=getattr(drawing_agent, "DEFAULT_STYLE_TEMPLATE", "patent_office"),
                    )

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
                st.markdown(f"#### {fig_number} {title}")
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
                    d1.download_button(tr("download") + " SVG", data=Path(svg_path).read_bytes(), file_name=Path(svg_path).name, mime="image/svg+xml")
                if png_path and Path(png_path).exists():
                    d2.download_button(tr("download") + " PNG", data=Path(png_path).read_bytes(), file_name=Path(png_path).name, mime="image/png")
                if json_path and Path(json_path).exists():
                    d3.download_button(tr("download") + " JSON", data=Path(json_path).read_bytes(), file_name=Path(json_path).name, mime="application/json")

    st.markdown('</div>', unsafe_allow_html=True)


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
        st.markdown(f"""
        <div class="chat-panel">
            <div class="chat-head">
                <span>{tr("chatbot_title")}</span>
                <span>AI</span>
            </div>
            <div class="chat-body">
        """, unsafe_allow_html=True)

        if not st.session_state.chat_msgs:
            st.markdown(f'<div class="chat-msg chat-bot">{tr("chatbot_welcome")}</div>', unsafe_allow_html=True)

        for role, msg in st.session_state.chat_msgs[-8:]:
            cls = "chat-user" if role == "user" else "chat-bot"
            st.markdown(f'<div class="chat-msg {cls}">{msg}</div>', unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

        user_msg = st.chat_input(tr("chatbot_ph"))
        if user_msg:
            target_page, ans = chatbot_answer(user_msg)
            answer_html = f'{ans} <a href="?page={target_page}&lang={lang}">→</a>'
            st.session_state.chat_msgs.append(("user", user_msg))
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


render_nav()

if page == "home":
    page_home()
elif page == "about":
    page_ready("nav_about")
elif page == "consultation":
    page_ready("nav_consultation")
elif page == "prior_art":
    page_ready("nav_prior_art")
elif page == "specification":
    page_ready("nav_specification")
elif page == "drawing":
    page_drawing()
elif page == "review":
    page_ready("nav_review")
elif page == "request":
    page_request()
elif page == "team":
    page_ready("nav_team")
elif page == "news":
    page_ready("nav_news")
elif page == "member_login":
    page_login(staff=False)
elif page == "staff_login":
    page_login(staff=True)
else:
    page_home()

render_footer()
render_chatbot()
