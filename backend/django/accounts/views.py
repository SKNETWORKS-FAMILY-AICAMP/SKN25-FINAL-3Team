import os
import sys
import json
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse, StreamingHttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .forms import LoginForm, SignupForm

_AGENT_PAGES = {
    'summary': {
        'num': 'II', 'name': '요약 에이전트', 'en': 'Summary Agent',
        'active': True, 'action_url': 'accounts:pipeline', 'action_label': '파이프라인에서 실행',
        'desc': '5개 발명 필드를 사람이 확인할 수 있는 요약본과 후속 에이전트용 구조화 발명 JSON으로 정리합니다.',
        'detail': '발명자가 입력한 5개 필드를 gpt-5.4 (또는 SUMMARY_AGENT_MODEL env)가 분석하여 readable_summary와 structured_invention JSON을 생성합니다. 이 JSON이 이후 모든 에이전트가 공유하는 PatentAgentState의 기반이 됩니다.',
        'inputs': ['프로젝트명 (project_name)', '해결하고자 하는 문제 (problem_to_solve)', '기존 기술의 문제점 (prior_art_problem)', '핵심 기술 구성 (core_technology)', '기대 효과 (expected_effect)'],
        'outputs': ['readable_summary — 사람이 확인하는 요약본', 'structured_invention JSON — 후속 에이전트용 구조화 데이터', '용어 후보 목록 (term_candidates)', 'warnings — 입력 부족 시 보완 요청'],
    },
    'prior-art': {
        'num': 'III', 'name': '선행기술조사 에이전트', 'en': 'Prior Art Agent',
        'active': True, 'action_url': 'accounts:pipeline', 'action_label': '파이프라인에서 실행',
        'desc': '특허 DB에서 text-embedding-3-small 임베딩 유사도 검색으로 선행문헌을 탐색하고, GPT-4o로 신규성·진보성 리스크를 분석해 보고합니다.',
        'detail': 'pgvector 기반 벡터 DB에서 text-embedding-3-small 임베딩으로 유사 특허를 탐색합니다. 검색된 선행문헌을 GPT-4o가 분석하여 발명과 겹치는 기술 요소(overlap_points), 차이점, 신규성·진보성 리스크를 평가합니다.',
        'inputs': ['draft_claim1 또는 발명 페이로드 (from 요약 에이전트)', 'pgvector 특허 DB 인덱스'],
        'outputs': ['선행문헌 후보 목록 (publication_no, title, analysis_summary)', '신규성 리스크 (novelty_risk)', '진보성 리스크 (inventive_step_risk)', 'overlap_points — 겹치는 기술 요소'],
    },
    'claim': {
        'num': 'IV', 'name': '청구항 에이전트', 'en': 'Claim Agent',
        'active': True, 'action_url': 'accounts:pipeline', 'action_label': '파이프라인에서 실행',
        'desc': '발명 구조를 분석해 독립항·종속항·방법항·시스템항을 특허청 작성 규정에 맞게 자동 생성합니다.',
        'detail': '요약·선행조사 결과를 바탕으로 특허청 규정에 맞는 청구항 구조를 설계합니다. 독립항 1개 이상, 이를 한정하는 종속항, 방법항, 시스템항을 자동 생성하며, 청구항 전략 메모도 함께 제공합니다.',
        'inputs': ['structured_invention JSON (from 요약 에이전트)', '선행기술 리스크 정보 (from 선행조사 에이전트)'],
        'outputs': ['독립항 (independent claims)', '종속항 (dependent claims)', '방법항 · 시스템항', '청구항 전략 메모'],
    },
    'drawing': {
        'num': 'V', 'name': '도면 에이전트', 'en': 'Drawing Agent',
        'active': True, 'action_url': 'accounts:drawing_gallery', 'action_label': '도면 생성하기',
        'desc': '블록도·흐름도·시퀀스 다이어그램을 SVG로 자동 렌더링하고 품질 점수 검수 및 자동 보정 후 파일을 제공합니다.',
        'detail': 'GPT-4o가 명세서 텍스트에서 도면 구조를 분석하여 블록도(block diagram), 흐름도(flowchart), 시퀀스 다이어그램 등을 SVG 형식으로 자동 렌더링합니다. 생성된 도면은 품질 점수(0-100)로 검수하고, 기준 미달 시 자동 보정을 거쳐 최종 파일을 제공합니다.',
        'inputs': ['특허 명세서 텍스트 (전체 또는 일부)', '출원 번호 (선택)'],
        'outputs': ['블록도 SVG', '흐름도 SVG', '품질 점수 및 등급 (S/A/B/C)', '자동 보정 여부'],
    },
    'specification': {
        'num': 'VI', 'name': '명세서 에이전트', 'en': 'Specification Agent',
        'active': True, 'action_url': 'accounts:pipeline', 'action_label': '파이프라인에서 실행',
        'desc': '기술분야·배경기술·해결수단·발명의 효과·상세설명 섹션을 특허 문체에 맞게 초안 작성합니다.',
        'detail': '특허청 규정에 맞는 5개 섹션을 자동 초안 작성합니다. 청구항·요약·도면 정보를 종합하여 일관된 문체와 참조부호 체계로 기술분야, 배경기술, 과제의 해결수단, 발명의 효과, 발명을 실시하기 위한 구체적인 내용을 생성합니다.',
        'inputs': ['structured_invention JSON', '청구항 초안 (from Claim 에이전트)', '도면 참조부호 정보 (from Drawing 에이전트)'],
        'outputs': ['기술분야 (technical_field)', '배경기술 (background_art)', '과제의 해결수단 (means_for_solving)', '발명의 효과 (effects)', '발명의 상세한 설명 (detailed_description)'],
    },
    'composer': {
        'num': 'VII', 'name': '컴포저 에이전트', 'en': 'Composer Agent',
        'active': True, 'action_url': 'accounts:pipeline', 'action_label': '파이프라인에서 실행',
        'desc': '전 에이전트 산출물을 병합·통일하고 용어·참조부호를 일관화해 제출 가능한 완성 명세서를 DOCX로 출력합니다.',
        'detail': 'LLM을 사용하지 않고, 앞선 에이전트들의 산출물(summary, prior_art, claims, drawings, specification)을 PatentAgentState에서 수집·병합하는 오케스트레이션 방식으로 동작합니다. abstract(요약서)는 청구항 1항 기반으로 규칙 생성하며, python-docx로 최종 DOCX 파일을 만들어 출력합니다.',
        'inputs': ['요약 · 선행조사 · 청구항 · 도면 · 명세서 모든 에이전트 산출물 (PatentAgentState)'],
        'outputs': ['완성 명세서 DOCX (python-docx)', '요약서 abstract (청구항 1항 기반 규칙 생성)', '최종 청구항 텍스트', 'composer_notes — 병합 과정 메모'],
    },
}

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_AGENTS = [
    {'num': 'I',   'name': '상담 에이전트',        'en': 'Consultation',  'active': False},
    {'num': 'II',  'name': '요약 에이전트',         'en': 'Summary',       'active': True},
    {'num': 'III', 'name': '선행기술조사 에이전트',  'en': 'Prior Art',     'active': True},
    {'num': 'IV',  'name': '청구항 에이전트',       'en': 'Claim',         'active': True},
    {'num': 'V',   'name': '도면 에이전트',         'en': 'Drawing',       'active': True},
    {'num': 'VI',  'name': '명세서 에이전트',       'en': 'Specification', 'active': True},
    {'num': 'VII', 'name': '컴포저 에이전트',       'en': 'Composer',      'active': True},
]


def landing(request):
    return render(request, 'accounts/landing.html', {
        'insights_preview': _PATENT_INSIGHTS,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = LoginForm(request, data=request.POST or None)
    error = None

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next') or 'accounts:landing')
        error = '아이디 또는 비밀번호가 올바르지 않습니다.'

    return render(request, 'accounts/login.html', {'form': form, 'error': error})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    form = SignupForm(request.POST or None)
    error = None

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(request.GET.get('next') or 'accounts:dashboard')
        error = '입력 정보를 다시 확인해주세요.'

    return render(request, 'accounts/signup.html', {'form': form, 'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('accounts:landing')


@login_required
def dashboard(request):
    if request.user.is_authenticated:
        return redirect('/workspace/dashboard/')
    return redirect('accounts:login')


def about_view(request):
    return render(request, 'pages/about.html')


def features_view(request):
    agents = [
        {'num': 'I',   'name': '상담 에이전트',        'en': 'Consultation',  'active': False,
         'desc': '발명 아이디어를 자연어로 입력받아 특허 가능성과 기술 구성을 분석합니다.',
         'url_name': 'accounts:agent_summary'},
        {'num': 'II',  'name': '요약 에이전트',         'en': 'Summary',       'active': True,
         'desc': '5개 발명 필드를 사람이 확인할 수 있는 요약본과 구조화 발명 JSON으로 정리합니다.',
         'url_name': 'accounts:agent_summary'},
        {'num': 'III', 'name': '선행기술조사 에이전트',  'en': 'Prior Art',     'active': False,
         'desc': '특허 DB에서 임베딩 유사도 검색으로 선행문헌을 탐색하고 리스크를 분석합니다.',
         'url_name': 'accounts:agent_prior_art'},
        {'num': 'IV',  'name': '청구항 에이전트',       'en': 'Claim',         'active': True,
         'desc': '발명 구조를 분석해 독립항·종속항·방법항·시스템항을 자동 생성합니다.',
         'url_name': 'accounts:agent_claim'},
        {'num': 'V',   'name': '도면 에이전트',         'en': 'Drawing',       'active': True,
         'desc': '블록도·흐름도를 SVG로 자동 렌더링하고 품질 점수 검수 및 보정 후 파일을 제공합니다.',
         'url_name': 'accounts:agent_drawing'},
        {'num': 'VI',  'name': '명세서 에이전트',       'en': 'Specification', 'active': True,
         'desc': '기술분야·배경기술·해결수단·발명의 효과·상세설명 섹션을 특허 문체로 초안 작성합니다.',
         'url_name': 'accounts:agent_specification'},
        {'num': 'VII', 'name': '컴포저 에이전트',       'en': 'Composer',      'active': True,
         'desc': '전 에이전트 산출물을 병합·통일하고 제출 가능한 완성 명세서를 출력합니다.',
         'url_name': 'accounts:agent_composer'},
    ]
    return render(request, 'pages/features.html', {'agents': agents})


def agents_overview_view(request):
    agents = [
        {'num': 'I',   'name': '상담 에이전트',        'en': 'Consultation',  'active': False,
         'desc': '발명 아이디어를 자연어로 입력받아 특허 가능성과 기술 구성을 분석합니다.',
         'url_name': 'accounts:agent_summary'},
        {'num': 'II',  'name': '요약 에이전트',         'en': 'Summary',       'active': True,
         'desc': '5개 발명 필드를 사람이 확인할 수 있는 요약본과 구조화 발명 JSON으로 정리합니다.',
         'url_name': 'accounts:agent_summary'},
        {'num': 'III', 'name': '선행기술조사 에이전트',  'en': 'Prior Art',     'active': False,
         'desc': '특허 DB에서 임베딩 유사도 검색으로 선행문헌을 탐색하고 리스크를 분석합니다.',
         'url_name': 'accounts:agent_prior_art'},
        {'num': 'IV',  'name': '청구항 에이전트',       'en': 'Claim',         'active': True,
         'desc': '발명 구조를 분석해 독립항·종속항·방법항·시스템항을 자동 생성합니다.',
         'url_name': 'accounts:agent_claim'},
        {'num': 'V',   'name': '도면 에이전트',         'en': 'Drawing',       'active': True,
         'desc': '블록도·흐름도를 SVG로 자동 렌더링하고 품질 점수 검수 및 보정 후 파일을 제공합니다.',
         'url_name': 'accounts:agent_drawing'},
        {'num': 'VI',  'name': '명세서 에이전트',       'en': 'Specification', 'active': True,
         'desc': '기술분야·배경기술·해결수단·발명의 효과·상세설명 섹션을 특허 문체로 초안 작성합니다.',
         'url_name': 'accounts:agent_specification'},
        {'num': 'VII', 'name': '컴포저 에이전트',       'en': 'Composer',      'active': True,
         'desc': '전 에이전트 산출물을 병합·통일하고 제출 가능한 완성 명세서를 출력합니다.',
         'url_name': 'accounts:agent_composer'},
    ]
    return render(request, 'pages/agents_overview.html', {'agents': agents})


_TEAM_DATA = {
    'kwon-gayoung': {
        'initial': '권', 'name': '권가영', 'slug': 'kwon-gayoung', 'photo': 'team/kwon-gayoung.jpg',
        'role': 'Consultation · Summary Agent',
        'role_ko': '상담·요약 에이전트',
        'desc': '상담 에이전트 및 요약 에이전트의 LLM 프롬프트 설계와 발명 정보 구조화 로직을 담당했습니다.',
        'detail': '발명자가 입력한 자연어 텍스트에서 특허 출원에 필요한 구조화 정보를 추출하는 상담 에이전트와, 5개 발명 필드를 후속 에이전트가 공유할 수 있는 structured_invention JSON으로 변환하는 요약 에이전트의 LLM 프롬프트를 설계했습니다. OpenAI Chat Completions API를 활용하여 발명 구성요소 자동 추출 및 용어 정규화 로직을 구현했습니다.',
        'skills': ['LLM Prompt Engineering', 'OpenAI API', 'Pydantic Schema Design', 'Python', 'LangGraph'],
        'agent': 'II', 'agent_name': '요약 에이전트', 'agent_url': 'accounts:agent_summary',
    },
    'kim-seohyun': {
        'initial': '김', 'name': '김서현', 'slug': 'kim-seohyun', 'photo': 'team/kim-seohyun.jpg',
        'role': 'Drawing Agent · Web UI',
        'role_ko': '도면 에이전트 · 웹 UI',
        'desc': '도면 에이전트 SVG 자동 생성 시스템과 Django 기반 웹 인터페이스 전체를 개발했습니다.',
        'detail': 'GPT-4o-mini/GPT-4o를 활용하여 특허 명세서 텍스트에서 블록도·흐름도 구조를 자동 추출하고 SVG로 렌더링하는 도면 에이전트를 구현했습니다. 품질 점수(0–100) 자동 검수 및 자동 보정 파이프라인을 포함하며, PYPI 웹 서비스 전체(랜딩·대시보드·파이프라인·채팅 등)를 Django 템플릿으로 설계·개발했습니다.',
        'skills': ['Django', 'GPT-4o', 'SVG Rendering', 'Python', 'CSS/JavaScript', 'LangGraph'],
        'agent': 'V', 'agent_name': '도면 에이전트', 'agent_url': 'accounts:agent_drawing',
    },
    'kim-hongik': {
        'initial': '김', 'name': '김홍익', 'slug': 'kim-hongik', 'photo': 'team/kim-hongik.jpg',
        'role': 'Prior Art Agent',
        'role_ko': '선행기술조사 에이전트',
        'desc': '선행기술조사 에이전트의 특허 DB 임베딩 검색 및 신규성·진보성 리스크 분석 시스템을 구현했습니다.',
        'detail': 'text-embedding-3-small 임베딩 모델과 pgvector 기반 벡터 DB를 활용하여 유사 특허를 탐색하는 선행기술조사 에이전트를 구현했습니다. GPT-4o를 통해 선행문헌의 청구항·요약을 분석하고 신규성 리스크(novelty_risk) 및 진보성 리스크(inventive_step_risk)를 정량적으로 평가하는 분석 파이프라인을 설계했습니다.',
        'skills': ['Vector DB (pgvector)', 'OpenAI Embeddings', 'GPT-4o', 'Python', 'Patent Analysis'],
        'agent': 'III', 'agent_name': '선행기술조사 에이전트', 'agent_url': 'accounts:agent_prior_art',
    },
    'park-beomsoo': {
        'initial': '박', 'name': '박범수', 'slug': 'park-beomsoo', 'photo': 'team/park-beomsoo.jpg',
        'role': 'Claim Agent',
        'role_ko': '청구항 에이전트',
        'desc': '청구항 에이전트 설계 및 특허청 규정 기반 독립항·종속항·방법항 자동 생성 로직을 구현했습니다.',
        'detail': '특허청 작성 규정(특허법 시행규칙)을 기반으로 발명 구조를 분석하여 독립항(independent claims)·종속항(dependent claims)·방법항·시스템항을 자동 생성하는 청구항 에이전트를 구현했습니다. ClaimDraft Pydantic 스키마를 설계하고 청구항 전략 메모 생성 기능을 포함했습니다.',
        'skills': ['Patent Law (특허법)', 'LLM Fine-tuning', 'Pydantic', 'Python', 'Claim Drafting'],
        'agent': 'IV', 'agent_name': '청구항 에이전트', 'agent_url': 'accounts:agent_claim',
    },
    'jo-eunseok': {
        'initial': '조', 'name': '조은석', 'slug': 'jo-eunseok', 'photo': 'team/jo-eunseok.jpg',
        'role': 'Specification Agent',
        'role_ko': '명세서 에이전트',
        'desc': '명세서 에이전트의 기술분야·배경기술·해결수단·발명의 효과 섹션 자동 초안 생성을 개발했습니다.',
        'detail': '특허 명세서의 핵심 5개 섹션(기술분야·배경기술·과제의 해결수단·발명의 효과·발명을 실시하기 위한 구체적인 내용)을 특허 문체에 맞게 자동 초안 작성하는 명세서 에이전트를 구현했습니다. 청구항·도면 참조부호를 연동하여 일관된 명세서를 생성하는 SpecificationMaterial 재료 수집 파이프라인을 설계했습니다.',
        'skills': ['Patent Writing', 'OpenAI API', 'Python', 'Specification Drafting', 'LangGraph'],
        'agent': 'VI', 'agent_name': '명세서 에이전트', 'agent_url': 'accounts:agent_specification',
    },
    'choi-hyunwoo': {
        'initial': '최', 'name': '최현우', 'slug': 'choi-hyunwoo', 'photo': 'team/choi-hyunwoo.jpg',
        'role': 'Project Lead · Composer Agent',
        'role_ko': 'PM · 컴포저 에이전트',
        'desc': '전체 멀티에이전트 아키텍처 설계 및 컴포저 에이전트의 최종 명세서 통합 파이프라인을 구성했습니다.',
        'detail': 'PYPI 전체 멀티에이전트 아키텍처(PatentAgentState 공유 상태, LangGraph 파이프라인)를 설계했습니다. 컴포저 에이전트는 모든 에이전트 산출물을 병합·통일하고 용어·참조부호·문체를 일관화하여 python-docx로 특허청 제출 가능한 DOCX 완성 명세서를 생성합니다.',
        'skills': ['LangGraph', 'Multi-Agent Architecture', 'Python', 'python-docx', 'Project Management'],
        'agent': 'VII', 'agent_name': '컴포저 에이전트', 'agent_url': 'accounts:agent_composer',
    },
}

def team_view(request):
    team = [
        {**v, 'url': f"/team/{v['slug']}/"}
        for v in _TEAM_DATA.values()
    ]
    return render(request, 'pages/team.html', {'team': team})


def team_member_view(request, slug):
    member = _TEAM_DATA.get(slug)
    if not member:
        raise Http404
    return render(request, 'pages/team_member.html', {'member': member})


_PATENT_INSIGHTS = [
    # ── 청구항 작성 ──────────────────────────────────────
    {
        'no': '01', 'tag': '청구항 작성',
        'title': '독립항과 종속항, 어떻게 구성해야 할까?',
        'summary': '특허 청구항의 핵심은 독립항의 범위 설정입니다. 독립항은 발명의 필수 구성요소만 포함해 최대한 넓은 보호 범위를 확보하고, 종속항으로 구체적인 실시예를 한정합니다.',
        'points': ['독립항: 필수 구성요소만 기재해 범위를 최대화', '종속항: 구체적 실시예·수치로 보완', '방법항·시스템항·제품항 병행 출원 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '02', 'tag': '청구항 작성',
        'title': '청구항 하나에 하나의 발명만 담아야 하는 이유',
        'summary': '단일성(unity of invention) 원칙에 따라 하나의 청구항에는 하나의 발명 개념만 포함해야 합니다. 여러 발명을 무리하게 합치면 심사 과정에서 분할출원 요구를 받을 수 있습니다.',
        'points': ['단일성 위반 시 심사관이 분할 요구', '기술적으로 연관된 발명은 선택적으로 묶기 가능', '분할출원으로 별도 보호 전략 수립'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '03', 'tag': '청구항 작성',
        'title': '기능적 표현(Means-Plus-Function) 청구항의 장단점',
        'summary': '"~를 위한 수단"과 같은 기능적 표현은 청구항 범위를 넓힐 수 있지만, 명세서에서 구체적 구현이 뒷받침되지 않으면 오히려 범위가 좁아지거나 무효가 됩니다.',
        'points': ['기능적 표현은 명세서 실시예로 지지 필수', '구조적 표현과 혼용해 범위 보완 가능', '소프트웨어 발명에서 활용 빈도 높음'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '04', 'tag': '청구항 작성',
        'title': '수치 한정 청구항 작성 시 주의사항',
        'summary': '수치 범위를 청구항에 포함하면 명확성이 높아지지만, 해당 범위 밖의 발명은 보호받지 못합니다. 실험 데이터를 충분히 확보한 후 범위를 설정해야 합니다.',
        'points': ['수치 범위는 실시예 데이터로 뒷받침', '지나치게 좁은 수치 한정은 회피 설계에 취약', '상·하한 모두 명확히 기재'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '05', 'tag': '청구항 작성',
        'title': '용어 정의(Claim Construction)의 중요성',
        'summary': '청구항에 사용된 용어는 명세서 전체와 일관되게 정의되어야 합니다. 용어의 의미가 불명확하면 특허 분쟁에서 불리하게 해석될 수 있습니다.',
        'points': ['명세서 서두에 주요 용어 정의 섹션 권장', '일반적 기술 용어 외 새로운 용어는 반드시 정의', '일관된 용어 사용이 침해 판단에 유리'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '06', 'tag': '청구항 작성',
        'title': '마커시 형식(Markush Group) 청구항의 활용',
        'summary': '화학·바이오 분야에서 "A, B 및 C로 이루어진 군에서 선택된"과 같은 마커시 형식을 사용하면 여러 화합물·성분을 하나의 청구항으로 포괄할 수 있습니다.',
        'points': ['화학·의약·소재 분야에서 광범위하게 활용', '군(group) 구성원들은 공통 특성을 가져야 함', 'KIPO·USPTO·EPO 모두 인정'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '07', 'tag': '청구항 작성',
        'title': '프로세스(방법) 청구항 vs 장치(시스템) 청구항',
        'summary': '동일한 기술 아이디어라도 방법 청구항과 장치 청구항으로 각각 출원하면 보호 범위가 확장됩니다. 방법 청구항은 공정·알고리즘에, 장치 청구항은 하드웨어·시스템 구조에 초점을 맞춥니다.',
        'points': ['방법 청구항: 단계별 순서가 핵심', '장치 청구항: 구성요소 간 연결 관계 명시', '두 유형 동시 출원으로 침해 대응 강화'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '08', 'tag': '청구항 작성',
        'title': '독립항 개수와 출원 비용의 상관관계',
        'summary': '특허청 출원료는 청구항 수에 따라 달라집니다. 독립항이 많을수록 비용은 늘지만 보호 범위도 넓어집니다. 핵심 독립항 3–5개, 종속항으로 세부 내용을 보완하는 전략이 효율적입니다.',
        'points': ['청구항 1~10항: 기본료 포함', '11항 이상: 항당 추가 비용 발생', '핵심 독립항 집중 후 종속항 확장 전략'],
        'agent': None, 'agent_url': None,
    },

    # ── 선행기술조사 ──────────────────────────────────────
    {
        'no': '09', 'tag': '선행기술조사',
        'title': '출원 전 선행기술조사가 반드시 필요한 이유',
        'summary': '선행기술조사 없이 출원하면 기존 특허와 충돌하여 거절될 수 있습니다. 유사 특허와의 차별점을 명확히 파악하고 청구항 전략을 수립하면 등록 가능성이 높아집니다.',
        'points': ['신규성·진보성 사전 검토 필수', '경쟁사 특허 동향 파악', '차별화 포인트 기반 청구항 전략 수립'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '10', 'tag': '선행기술조사',
        'title': 'KIPRIS로 무료 선행기술조사 하는 법',
        'summary': 'KIPRIS(특허정보검색서비스)는 국내 특허·실용신안·디자인·상표를 무료로 검색할 수 있는 공식 DB입니다. IPC 분류코드와 키워드를 조합하면 정밀한 조사가 가능합니다.',
        'points': ['IPC 코드 + 키워드 조합 검색 권장', '출원인·발명자 이름으로 경쟁사 동향 파악', '영문 검색은 esp@cenet(EPO) 병행'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '11', 'tag': '선행기술조사',
        'title': '국제 특허 DB 활용법: Google Patents vs Espacenet',
        'summary': 'Google Patents는 직관적 인터페이스와 AI 번역 기능으로 접근성이 높고, Espacenet은 유럽특허청의 공식 DB로 분류코드 검색과 패밀리 특허 조회에 강점이 있습니다.',
        'points': ['Google Patents: AI 번역·유사특허 추천 기능', 'Espacenet: IPC/CPC 코드 심층 검색', 'USPTO Full-Text: 미국 특허 원문 검색'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '12', 'tag': '선행기술조사',
        'title': '선행기술 발견 시 청구항 전략 수정하는 방법',
        'summary': '유사한 선행기술이 발견되면 공황 상태가 될 수 있지만, 차별점을 찾아 청구항을 수정하면 여전히 등록이 가능합니다. 선행기술 대비 기술적 우위를 명세서에 명확히 서술하는 것이 핵심입니다.',
        'points': ['선행기술과 차이점을 배경기술 섹션에 명시', '기술적 효과의 현저한 차이 강조', '종속항으로 세부 구성 차별화'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '13', 'tag': '선행기술조사',
        'title': 'FTO(Freedom to Operate) 분석이란?',
        'summary': 'FTO는 특정 제품이나 기술을 시장에 출시할 때 타인의 유효한 특허를 침해하지 않는지 사전에 검토하는 분석입니다. 제품 출시 전 반드시 실시해야 리스크를 줄일 수 있습니다.',
        'points': ['제품 출시 전·투자 유치 전 필수 분석', '해당 국가에서 유효한 특허만 대상', '회피 설계 가능 여부 함께 검토'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '14', 'tag': '선행기술조사',
        'title': '특허 패밀리(Patent Family) 조사의 전략적 가치',
        'summary': '하나의 발명은 여러 국가에서 동시에 출원될 수 있으며 이를 특허 패밀리라 합니다. 경쟁사의 패밀리를 추적하면 글로벌 IP 전략을 파악하고 대응 전략을 수립할 수 있습니다.',
        'points': ['Derwent Innovation으로 패밀리 분석', '경쟁사 핵심 특허의 보호 국가 파악', '공백 국가에 선제적 출원 전략 가능'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 도면 ──────────────────────────────────────
    {
        'no': '15', 'tag': '특허 도면',
        'title': '특허 도면의 규격과 품질 기준',
        'summary': '특허청은 도면에 대해 엄격한 규격을 요구합니다. 선 굵기, 참조부호 표기 방식, 도면 번호 체계 등이 규정에 맞지 않으면 보정 명령을 받을 수 있습니다.',
        'points': ['흑백 선도(line drawing) 원칙', '참조부호는 아라비아 숫자 사용', '도 1, 도 2 순서로 번호 부여'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '16', 'tag': '특허 도면',
        'title': '흐름도(Flowchart) 도면 작성 시 핵심 원칙',
        'summary': '소프트웨어·방법 발명에서 흐름도는 청구항의 각 단계를 시각화하는 핵심 도면입니다. 각 단계는 박스로, 조건 분기는 다이아몬드 형태로 표현하며 참조부호를 반드시 부여해야 합니다.',
        'points': ['각 단계 박스마다 참조부호 부여', '흐름 방향은 위→아래 또는 좌→우 일관성 유지', '청구항의 단계 순서와 일치해야 함'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '17', 'tag': '특허 도면',
        'title': '블록도(Block Diagram) 도면으로 시스템 구조 표현하기',
        'summary': '하드웨어 시스템·네트워크 구조 특허에서 블록도는 구성요소 간 연결과 신호 흐름을 보여줍니다. 각 블록은 청구항의 구성요소와 1:1로 대응되어야 명확성을 유지할 수 있습니다.',
        'points': ['각 블록은 청구항 구성요소와 대응', '신호 흐름은 화살표로 방향 표시', '복잡한 시스템은 계층별 도면으로 분리'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '18', 'tag': '특허 도면',
        'title': '도면 보정(Amendment) 없이 최초 제출하는 전략',
        'summary': '도면 보정은 추가 비용과 시간이 소요됩니다. 출원 전 도면 규격을 철저히 준수하고 AI 도구를 활용해 사전 검수하면 보정 없이 심사를 통과할 확률이 높아집니다.',
        'points': ['KIPO 도면 작성 매뉴얼 사전 숙지', 'AI 도면 생성 도구로 규격 자동 준수', '제출 전 참조부호 누락 여부 체크리스트 확인'],
        'agent': None, 'agent_url': None,
    },

    # ── 명세서 작성 ──────────────────────────────────────
    {
        'no': '19', 'tag': '명세서 작성',
        'title': '발명의 설명 섹션을 구성하는 5가지 원칙',
        'summary': '특허 명세서의 발명의 설명은 기술분야·배경기술·해결수단·발명의 효과·실시예 5개 섹션으로 구성됩니다. 각 섹션은 청구항과 논리적으로 일치해야 등록 가능성이 높아집니다.',
        'points': ['청구항과 명세서의 논리적 일관성 유지', '실시예는 청구항 구성요소의 구체화', '수치·범위는 명확하게 기재'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '20', 'tag': '명세서 작성',
        'title': '배경기술 섹션, 어떻게 써야 진보성에 유리한가?',
        'summary': '배경기술 섹션에서 기존 기술의 문제점을 명확히 서술할수록 본 발명의 진보성이 자연스럽게 부각됩니다. 단순히 기존 기술 소개에 그치지 말고, 해결되지 않은 과제를 중심으로 기술해야 합니다.',
        'points': ['종래 기술의 한계·단점을 구체적으로 기술', '과제 해결 흐름이 논리적이어야 함', '인용 선행기술 문헌은 정확한 출처 표기'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '21', 'tag': '명세서 작성',
        'title': '실시예(Embodiment) 개수는 얼마나 필요한가?',
        'summary': '실시예는 발명의 구체적 구현 방법을 설명하며, 하나의 핵심 실시예와 대안적 실시예를 함께 기재하면 청구항 범위를 충분히 뒷받침할 수 있습니다.',
        'points': ['핵심 실시예 1개 이상 필수', '대안 실시예로 청구항 범위 커버', '도면과 실시예의 참조부호 일치 필수'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '22', 'tag': '명세서 작성',
        'title': '발명의 효과(Advantageous Effects) 섹션 작성법',
        'summary': '발명의 효과 섹션은 단순히 "빠르다", "편리하다"는 표현보다 수치화된 개선 효과를 기재하면 심사관 설득력이 높아집니다. 비교 실험 데이터를 포함하면 더욱 효과적입니다.',
        'points': ['정량적 수치(%, 배율) 표현 활용', '선행기술 대비 개선 효과 명시', '예상 효과가 아닌 실험·시뮬레이션 결과 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '23', 'tag': '명세서 작성',
        'title': '요약서(Abstract) 작성 전략',
        'summary': '요약서는 검색 엔진에 노출되는 첫 번째 텍스트입니다. 150단어(국내) 이내로 기술분야·해결 과제·해결 수단·주요 효과를 압축적으로 담아야 합니다.',
        'points': ['150자(한국) 이내로 간결하게 작성', '청구항 제1항의 핵심 내용 반영', '검색 키워드를 자연스럽게 포함'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '24', 'tag': '명세서 작성',
        'title': '컴퓨터 구현 발명(CII) 명세서 작성 특수 사항',
        'summary': '소프트웨어·AI 발명은 "컴퓨터에서 실행되는" 명확한 기술적 특징을 기재해야 특허적격성을 충족합니다. 추상적 아이디어에 그치지 않도록 구체적 구현과 기술적 효과를 명확히 해야 합니다.',
        'points': ['기술적 문제와 기술적 해결 수단 명확히 연결', '하드웨어 구성(프로세서, 메모리) 명시 권장', '알고리즘은 단계별 프로세스로 상세 기술'],
        'agent': None, 'agent_url': None,
    },

    # ── 출원 절차 ──────────────────────────────────────
    {
        'no': '25', 'tag': '출원 절차',
        'title': '국내 특허 출원 절차 한눈에 보기',
        'summary': '특허 출원부터 등록까지는 평균 2–3년이 소요됩니다. 출원→심사청구→방식심사→실체심사→등록결정의 단계를 이해하면 전략적으로 대응할 수 있습니다.',
        'points': ['출원 후 심사청구: 3년 이내 필수', '우선심사 신청 시 6–12개월 단축 가능', '거절이유 통지 후 의견서·보정서 제출'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '26', 'tag': '출원 절차',
        'title': '우선심사 신청 자격과 활용 전략',
        'summary': '우선심사는 일반 심사보다 빠르게 결과를 받을 수 있는 제도입니다. 공익상 필요, 긴급 처리 필요, 중소기업 특례 등 요건을 충족하면 신청할 수 있습니다.',
        'points': ['중소기업·스타트업 우선심사 신청 가능', '실시 또는 실시 준비 중인 발명 우선 대상', '신청 후 약 6개월 내 심사 결과 수령'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '27', 'tag': '출원 절차',
        'title': '특허 출원일의 중요성: 선출원주의란?',
        'summary': '한국을 포함한 대부분의 국가는 선출원주의를 채택합니다. 동일한 발명이 두 명에게서 나왔을 때 먼저 출원한 사람이 특허권을 갖습니다. 발명 완성 즉시 출원하는 것이 최선입니다.',
        'points': ['동일 발명은 가장 먼저 출원한 자가 권리 취득', '미국만 예외적으로 선발명주의 일부 유지', '가출원(임시출원)으로 출원일 선점 전략 활용'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '28', 'tag': '출원 절차',
        'title': '분할출원과 변경출원으로 보호 범위 넓히기',
        'summary': '원출원의 명세서에 기재된 내용 범위 내에서 분할출원을 통해 추가적인 청구항을 확보할 수 있습니다. 등록 후에도 전략적으로 분할출원을 활용해 경쟁사 진입을 차단할 수 있습니다.',
        'points': ['분할출원은 원출원의 출원일 소급 적용', '등록 전까지 분할출원 가능', '원출원에 공개된 실시예 기반으로만 권리 범위 설정'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '29', 'tag': '출원 절차',
        'title': '거절이유통지서(OA) 대응 전략',
        'summary': '심사관의 거절이유통지서는 특허 등록의 마지막 관문입니다. 신규성·진보성·기재불비 등 거절 유형별로 대응 전략이 다르며, 의견서와 보정서를 적절히 활용해야 합니다.',
        'points': ['신규성 거절: 선행기술과 구별점 부각', '진보성 거절: 기술적 효과의 현저성 논증', '기재불비: 명세서·청구항 보정으로 해결'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '30', 'tag': '출원 절차',
        'title': '특허 등록 후 연차료 납부 일정과 주의사항',
        'summary': '특허권은 등록 후 매년 연차료를 납부해야 유지됩니다. 납부 기간을 놓치면 특허권이 소멸할 수 있으며, 추납 기간 내에는 과태료를 내고 회복이 가능합니다.',
        'points': ['등록 후 3년차부터 연차료 납부 시작', '납부 기간 경과 후 6개월 이내 추납 가능', '전략적으로 불필요한 특허는 포기 고려'],
        'agent': None, 'agent_url': None,
    },

    # ── 신규성·진보성 ──────────────────────────────────────
    {
        'no': '31', 'tag': '신규성·진보성',
        'title': '신규성(Novelty) 판단 기준 완전 정리',
        'summary': '신규성은 출원 전 공중에 알려지지 않은 발명이어야 한다는 요건입니다. 논문 발표, 제품 판매, 전시회 발표 등이 모두 신규성 상실 사유가 됩니다.',
        'points': ['출원 전 1년 내 공개는 신규성 의제 적용 가능', '발명자 본인의 공개도 신규성 상실 원인', '비밀 유지 계약(NDA) 체결 후 공개 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '32', 'tag': '신규성·진보성',
        'title': '진보성(Inventive Step) 심사에서 승리하는 법',
        'summary': '진보성은 통상의 기술자가 선행기술로부터 쉽게 발명할 수 없어야 한다는 요건입니다. 선행기술들을 결합해도 본 발명에 이를 수 없음을 기술적 효과로 설득하는 것이 핵심입니다.',
        'points': ['선행기술 조합의 어려움(motivation 부재) 논증', '예측하지 못한 기술적 효과(synergy) 강조', '수치 범위의 임계적 의의 증명'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '33', 'tag': '신규성·진보성',
        'title': '공지예외(신규성 의제) 제도 활용법',
        'summary': '발명자가 출원 전 논문이나 학회에 발표한 경우, 출원일로부터 12개월(국내) 이내에 공지예외 적용 신청을 하면 신규성 상실을 막을 수 있습니다.',
        'points': ['출원일로부터 12개월 소급 적용', '공지예외 적용 신청서 및 증명서류 제출 필수', '미국 AIA 기준 12개월 그레이스 기간 적용'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '34', 'tag': '신규성·진보성',
        'title': '선택발명(Selection Invention)으로 기존 특허 포위망 돌파',
        'summary': '상위 개념으로 이미 특허가 존재해도, 그 하위 범주에서 현저한 기술적 효과가 있는 발명은 선택발명으로 등록 가능합니다. 화학·제약 분야에서 특히 유용한 전략입니다.',
        'points': ['상위 개념 특허의 범위 내에 있어도 등록 가능', '현저한 효과(임계적 의의)가 반드시 필요', '화학식·조성물 발명에서 주로 활용'],
        'agent': None, 'agent_url': None,
    },

    # ── PCT 국제출원 ──────────────────────────────────────
    {
        'no': '35', 'tag': 'PCT 국제출원',
        'title': 'PCT 출원으로 30개월 내 국제 보호 전략 수립하기',
        'summary': 'PCT(Patent Cooperation Treaty) 출원은 하나의 출원서로 150개 이상 국가에 동시에 출원일을 확보할 수 있는 제도입니다. 국내 우선일로부터 12개월 이내에 PCT 출원을 해야 합니다.',
        'points': ['우선일로부터 30개월 내 각국 국내단계 진입 결정', 'WIPO 국제사무국에 1건의 출원서 제출', '국제조사보고서(ISR)로 등록 가능성 사전 파악'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '36', 'tag': 'PCT 국제출원',
        'title': '파리조약(Paris Convention) 우선권과 PCT의 차이',
        'summary': '파리조약 우선권은 첫 출원일로부터 12개월 이내에 타국에 직접 출원하는 방식이며, PCT는 중간 단계를 통해 30개월까지 각국 진입을 연장할 수 있습니다. 비용과 시간에 따라 전략적으로 선택해야 합니다.',
        'points': ['파리조약: 12개월 내 각국 직접 출원', 'PCT: 30개월까지 국내단계 진입 결정 유예', '타겟 시장이 명확하면 파리조약, 불확실하면 PCT'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '37', 'tag': 'PCT 국제출원',
        'title': '미국(USPTO) 출원 시 반드시 알아야 할 사항',
        'summary': '미국 특허는 출원 후 18개월 비공개 신청, 가출원(Provisional Application), 계속출원(Continuation) 등 독특한 제도가 있습니다. AIA 이후 선출원주의로 전환됐지만 세부 규정은 여전히 복잡합니다.',
        'points': ['가출원으로 12개월 우선일 확보 후 정규출원', '계속출원으로 청구항 범위 확장 가능', 'Information Disclosure Statement(IDS) 의무 제출'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '38', 'tag': 'PCT 국제출원',
        'title': '유럽 특허(EPO) 출원 전략과 검증',
        'summary': 'EPO(유럽특허청) 등록 특허는 지정국에서 개별 검증(validation)을 거쳐야 각국에서 효력이 발생합니다. 유니타리 특허(UP) 제도 도입으로 일부 EU 국가에서는 단일 특허 효력이 가능해졌습니다.',
        'points': ['주요 유럽 시장 우선 지정(DE, FR, GB, NL)', '유니타리 특허로 25개국 단일 효력 가능', '번역·공증 비용 국가별 상이'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '39', 'tag': 'PCT 국제출원',
        'title': '중국 특허 출원의 특수성과 주의사항',
        'summary': '중국 특허는 출원에서 등록까지 약 2–3년이 소요되며, 중문 번역의 정확성이 권리 범위에 직접 영향을 미칩니다. 발명특허 외에도 실용신형(Utility Model) 제도를 전략적으로 활용할 수 있습니다.',
        'points': ['실용신형은 심사 없이 18개월 내 등록', '발명특허와 실용신형 동시 출원 전략 가능', '중문 번역 오류가 권리 소멸 원인이 될 수 있음'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '40', 'tag': 'PCT 국제출원',
        'title': '일본 특허(JPO) 출원 시 출원인이 주의할 사항',
        'summary': '일본 특허는 심사 품질이 높고 심사관의 선행기술 조사가 철저합니다. 청구항 범위 조정 요구가 많으므로 처음부터 여러 개의 독립항을 준비하는 전략이 유효합니다.',
        'points': ['일본어 번역 품질이 권리 범위 결정', '실용신안(실용신형) 제도 활용 가능', '중간 처리 비용 사전 예산 책정 필요'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 전략 ──────────────────────────────────────
    {
        'no': '41', 'tag': '특허 전략',
        'title': '특허 포트폴리오 구축의 기초 전략',
        'summary': '단일 특허 하나보다 핵심 기술을 중심으로 방사형 포트폴리오를 구축하면 경쟁사의 회피 설계를 방지할 수 있습니다. 핵심 특허 주변에 개량 발명을 쌓아 방어막을 형성합니다.',
        'points': ['핵심 기술 1건 + 주변 개량특허 다수', '경쟁사 제품 분석 후 공백 기술 출원', '라이선스·매각을 고려한 포트폴리오 설계'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '42', 'tag': '특허 전략',
        'title': '방어적 공개(Defensive Publication)의 전략적 활용',
        'summary': '특허로 등록하지 않더라도 기술을 공개하면 선행기술로 등재되어 타인이 동일 기술을 특허화하는 것을 막을 수 있습니다. 유지 비용 없이 경쟁사의 특허 취득을 저지하는 유력한 전략입니다.',
        'points': ['IP.com, ArXiv 등 공개 플랫폼 활용', '공개 즉시 전 세계 선행기술로 효력 발생', '영업비밀 유지가 더 유리한 경우는 제외'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '43', 'tag': '특허 전략',
        'title': '스타트업의 IP 전략: 한정된 예산으로 최대 보호',
        'summary': '스타트업은 핵심 기술 1–2건에 집중 투자하고, 나머지는 영업비밀 또는 방어적 공개로 관리하는 것이 효율적입니다. 투자 유치와 M&A를 고려한 IP 포트폴리오 구성이 중요합니다.',
        'points': ['핵심 기술 1–2건 우선 출원', '나머지는 방어적 공개로 선행기술 등재', '투자자가 중요시하는 IP 현황 문서 정비'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '44', 'tag': '특허 전략',
        'title': '특허 맵(Patent Map)으로 기술 트렌드 읽기',
        'summary': '특허 맵은 특정 기술 분야의 출원 동향, 핵심 출원인, 기술 공백 영역을 한눈에 보여주는 분석 도구입니다. 신규 R&D 방향 설정과 경쟁사 IP 전략 파악에 필수적입니다.',
        'points': ['연도별 출원 건수로 기술 성숙도 파악', '출원인 분석으로 경쟁사 R&D 방향 예측', '기술 공백 영역에 선제적 출원 기회 발굴'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '45', 'tag': '특허 전략',
        'title': '크로스 라이선스(Cross-License) 협상 전략',
        'summary': '두 기업이 상호 보유한 특허를 서로 실시할 수 있도록 라이선스를 교환하는 크로스 라이선스는 특허 분쟁을 합리적으로 해결하는 방법입니다. 유사한 규모의 포트폴리오를 보유할 때 유리합니다.',
        'points': ['포트폴리오 규모·품질이 협상력을 결정', '계약서에 실시 범위·기간·지역 명확히 규정', '분쟁 예방과 기술 협력 동시 달성 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '46', 'tag': '특허 전략',
        'title': '특허 양도·라이선스로 수익 창출하기',
        'summary': '특허를 직접 실시하지 않더라도 라이선스 계약으로 로열티를 수령하거나 양도를 통해 일시금을 받을 수 있습니다. 대학·연구소 보유 특허의 기술이전은 중요한 수익원입니다.',
        'points': ['전용실시권과 통상실시권의 차이 이해', '로열티율은 매출액의 2–8% 수준이 일반적', '기술이전 전문 플랫폼(NTIS, 기술거래소) 활용'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 분쟁 ──────────────────────────────────────
    {
        'no': '47', 'tag': '특허 분쟁',
        'title': '특허 침해 판단 기준: 문언 침해와 균등론',
        'summary': '특허 침해는 청구항의 구성요소를 전부 실시하는 경우(문언 침해) 또는 일부를 균등한 수단으로 대체해도 동일한 효과를 내는 경우(균등론)에 성립합니다.',
        'points': ['전 요소 충족(All Elements Rule) 원칙', '균등론: 치환 가능성·동일 작용 효과 판단', '파일 히스토리 에스토펠로 균등론 제한 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '48', 'tag': '특허 분쟁',
        'title': '특허 무효심판 청구 전략',
        'summary': '경쟁사 특허가 신규성·진보성 흠결이 있다면 특허심판원에 무효심판을 청구할 수 있습니다. 침해 소송을 당한 경우 반소로 무효심판을 제기하는 것이 효과적인 방어 전략입니다.',
        'points': ['무효 증거: 출원 전 공개된 선행기술 발굴', '청구항 전체 무효보다 일부 청구항 무효 전략', '특허심판원 → 특허법원 → 대법원 순으로 상소'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '49', 'tag': '특허 분쟁',
        'title': '특허 침해 경고장 수령 시 대응 절차',
        'summary': '경고장을 받으면 무시하지 말고 즉시 전문가와 상담해야 합니다. 침해 여부를 검토하고, 라이선스 협상·무효심판 청구·회피 설계 중 최적의 전략을 선택해야 합니다.',
        'points': ['수령 후 즉시 IP 전문 변호사·변리사 상담', '해당 특허 청구항 분석 및 침해 여부 검토', '무효 자료 수집, 회피 설계 검토 병행'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '50', 'tag': '특허 분쟁',
        'title': 'NPE(특허괴물) 대응 전략',
        'summary': 'NPE(Non-Practicing Entity)는 특허를 직접 실시하지 않고 로열티 수익만을 목적으로 하는 특허 전문 기업입니다. 조기 합의, 무효화, 회피 설계 중 비용 대비 최적 전략을 선택해야 합니다.',
        'points': ['NPE 특허의 무효율이 상대적으로 높음', '소송 비용 vs 합의금 비교 분석 필수', 'IPR(Inter Partes Review)로 특허 무효화 도전'],
        'agent': None, 'agent_url': None,
    },

    # ── 직무발명 ──────────────────────────────────────
    {
        'no': '51', 'tag': '직무발명',
        'title': '직무발명 보상 제도의 기본 개념',
        'summary': '직원이 업무 수행 중 완성한 발명은 직무발명에 해당하며, 사용자는 이를 승계받는 대신 정당한 보상을 지급해야 합니다. 보상 규정이 없으면 법적 분쟁으로 이어질 수 있습니다.',
        'points': ['직무발명: 업무 범위 내 발명', '출원 보상·등록 보상·실시 보상으로 구분', '보상 규정은 취업규칙·단체협약에 명시 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '52', 'tag': '직무발명',
        'title': '직무발명 예약 승계 조항의 유효성',
        'summary': '근로계약서나 취업규칙에 직무발명을 사용자가 자동으로 승계한다는 조항을 넣으면 법적으로 유효합니다. 단, 정당한 보상이 없으면 무효로 판단될 수 있으므로 보상 체계를 함께 마련해야 합니다.',
        'points': ['예약 승계 조항 + 보상 규정 동시 마련 필수', '정당 보상 없는 예약 승계는 무효 판결 가능성', '발명신고서 제출 절차 규정 운영 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '53', 'tag': '직무발명',
        'title': '퇴직 후 직무발명 분쟁 예방법',
        'summary': '퇴직 후 전 직원이 회사 재직 중 완성한 발명으로 특허를 출원하는 경우 분쟁이 발생할 수 있습니다. 퇴직 시 발명 정산 동의서와 보안 유지 서약서를 확보하는 것이 중요합니다.',
        'points': ['퇴직 시 발명 정산 동의서 확보', '재직 중 발명 목록 관리(발명신고서) 철저히', '퇴직 후 1년 이내 출원 시 직무발명 추정'],
        'agent': None, 'agent_url': None,
    },

    # ── AI·소프트웨어 특허 ──────────────────────────────────────
    {
        'no': '54', 'tag': 'AI·SW 특허',
        'title': 'AI 발명의 특허 적격성 판단 기준',
        'summary': 'AI 알고리즘 자체는 추상적 아이디어로 특허 적격성이 없지만, 구체적 기술 문제를 해결하는 수단으로 명세서를 구성하면 특허를 취득할 수 있습니다. 기술적 효과를 중심으로 청구항을 작성하는 것이 핵심입니다.',
        'points': ['추상적 알고리즘 → 기술적 수단으로 전환', '입력-처리-출력의 구체적 구현 명시', '기술적 효과(속도 향상, 오류 감소)를 수치로 기재'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '55', 'tag': 'AI·SW 특허',
        'title': '머신러닝 모델 특허화 전략',
        'summary': '머신러닝 모델의 학습 방법, 추론 방법, 데이터 전처리 방법, 모델 구조 등을 각각 별도 청구항으로 분리하면 폭넓은 보호가 가능합니다. 모델 구조는 시스템 청구항으로, 학습 방법은 방법 청구항으로 구성합니다.',
        'points': ['학습 방법·추론 방법·모델 구조 각각 별도 청구', '데이터 증강·전처리 방법도 독립 출원 가치 있음', '성능 지표(정확도, F1 score) 수치 기재로 진보성 보완'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '56', 'tag': 'AI·SW 특허',
        'title': 'LLM 기반 발명의 청구항 작성 전략',
        'summary': '대형 언어 모델(LLM) 활용 발명은 프롬프트 엔지니어링, 파인튜닝 방법, RAG 파이프라인, 멀티에이전트 시스템 등 다양한 관점에서 특허화할 수 있습니다. 각 기술 레이어를 분리해 출원하면 효과적입니다.',
        'points': ['프롬프트 구조·체계가 기술적 구현에 해당', '파인튜닝 데이터 처리 방법 별도 출원 가능', 'RAG 검색-증강 파이프라인은 시스템 특허로 보호'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '57', 'tag': 'AI·SW 특허',
        'title': 'AI 발명자 문제: AI가 발명을 했다면 특허 주체는?',
        'summary': 'DABUS 사건 이후 전 세계적으로 AI를 발명자로 기재할 수 없다는 판결이 내려지고 있습니다. 현재는 AI를 활용한 인간 발명자가 특허 출원인이 되어야 합니다.',
        'points': ['현행법상 발명자는 자연인(인간)만 가능', 'AI 보조 발명 시 실질적 기여한 인간을 발명자로', 'WIPO 2025 가이드라인: AI 기여도 표시 권장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '58', 'tag': 'AI·SW 특허',
        'title': '소프트웨어 특허 vs 저작권: 무엇으로 보호할까?',
        'summary': '소프트웨어는 특허와 저작권 모두로 보호 가능하지만 보호 대상이 다릅니다. 특허는 기능·알고리즘·방법을, 저작권은 코드 자체 표현을 보호합니다. 두 가지를 함께 활용하면 포괄적 보호가 가능합니다.',
        'points': ['특허: 기능·아이디어 보호 (20년)', '저작권: 소스코드 표현 보호 (창작 후 70년)', '영업비밀로 핵심 알고리즘 보호 병행 전략'],
        'agent': None, 'agent_url': None,
    },

    # ── 바이오·의약 특허 ──────────────────────────────────────
    {
        'no': '59', 'tag': '바이오·의약 특허',
        'title': '의약 용도발명 특허화 전략',
        'summary': '이미 알려진 물질이라도 새로운 의약 용도를 발견하면 용도발명으로 특허를 취득할 수 있습니다. 청구항에 투여 대상, 투여량, 투여 방법을 구체화하면 범위와 유효성을 높일 수 있습니다.',
        'points': ['알려진 물질의 새로운 치료 용도 보호 가능', '투여량·용법을 청구항에 명시해 범위 차별화', '임상 데이터가 진보성 입증에 결정적'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '60', 'tag': '바이오·의약 특허',
        'title': 'mRNA 특허 만료와 바이오시밀러 기회',
        'summary': '2026년부터 순차적으로 mRNA 핵심 특허가 만료되면서 제네릭·바이오시밀러 진입 기회가 열립니다. 특허 클리프(Patent Cliff)를 선제적으로 파악하고 후발 기업의 시장 진입 전략을 수립해야 합니다.',
        'points': ['특허 만료 일정 사전 추적(Orange Book 등)', '용도·제형·투여 방법 특허는 별도 존속 가능', '바이오시밀러 승인 절차는 일반 제네릭과 상이'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '61', 'tag': '바이오·의약 특허',
        'title': '유전자 치료제 특허의 청구 범위 설정',
        'summary': '유전자 편집(CRISPR), 세포 치료제(CAR-T), 유전자 전달 벡터 등 바이오테크 분야는 물질특허·방법특허·용도특허가 복잡하게 얽혀 있습니다. 최초 기술 발굴 단계부터 다층적 특허 전략이 필요합니다.',
        'points': ['물질(핵산 서열)·방법·용도 각각 독립 출원', 'CRISPR gRNA 서열 자체의 특허 가능성 검토', '바이오 분야는 광범위 청구가 무효 위험도 높음'],
        'agent': None, 'agent_url': None,
    },

    # ── 반도체·전자 특허 ──────────────────────────────────────
    {
        'no': '62', 'tag': '반도체·전자 특허',
        'title': 'HBM·PIM 특허 전쟁이 시사하는 점',
        'summary': '고대역폭 메모리(HBM)와 PIM 분야에서 삼성·SK하이닉스·마이크론의 특허 분쟁은 핵심 기술의 선점 출원 전략이 시장 주도권을 결정한다는 것을 보여줍니다.',
        'points': ['신규 기술은 양산 전 특허 포트폴리오 완성', '핵심 구조 특허 + 제조 방법 특허 병행', '표준특허(SEP) 편입 전략으로 라이선스 수익화'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '63', 'tag': '반도체·전자 특허',
        'title': '표준필수특허(SEP) 전략과 FRAND 의무',
        'summary': '기술 표준에 채택된 SEP(Standard Essential Patent) 보유자는 합리적·비차별적(FRAND) 조건으로 라이선스를 제공할 의무가 있습니다. 표준특허 포트폴리오는 막대한 로열티 수익으로 이어집니다.',
        'points': ['ETSI, ITU, IEEE 등 표준화 기구에 SEP 신고', 'FRAND 조건 위반 시 특허권 남용으로 항변 가능', '5G·와이파이·블루투스 분야 SEP 경쟁 치열'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '64', 'tag': '반도체·전자 특허',
        'title': '전고체 배터리 특허 선점 경쟁 현황',
        'summary': '토요타(1,000건+), 삼성SDI, CATL 등이 전고체 배터리 핵심 특허를 대규모로 선점 중입니다. 고체 전해질, 인터페이스 개선, 제조 공정 등 세부 기술별 특허 공백을 파악하는 것이 전략의 출발점입니다.',
        'points': ['고체 전해질 소재·제조 방법 핵심 특허', '양극재·음극재 인터페이스 개선 특허 공백 존재', '2027년 양산 전 핵심 포지션 확보 시급'],
        'agent': None, 'agent_url': None,
    },

    # ── 디자인권·상표권 ──────────────────────────────────────
    {
        'no': '65', 'tag': '디자인권',
        'title': '디자인권으로 제품 외관 보호하기',
        'summary': '제품의 외관(형상, 모양, 색채)은 특허 대신 디자인권으로 보호할 수 있습니다. 특허보다 등록이 쉽고 빠르며, 제품 출시 전 반드시 출원해야 신규성을 유지할 수 있습니다.',
        'points': ['디자인권 존속기간: 등록일로부터 20년', '특허와 디자인 동시 출원으로 이중 보호 가능', 'UI·아이콘 등 화상 디자인도 보호 대상'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '66', 'tag': '상표권',
        'title': '상표 출원 전 유사 상표 조사하는 방법',
        'summary': '상표 출원 전 KIPRIS 상표 검색으로 동일·유사한 선등록 상표가 있는지 반드시 확인해야 합니다. 유사 상표가 있으면 거절되거나 분쟁이 발생할 수 있습니다.',
        'points': ['KIPRIS 유사 상표 사전 조사 필수', '상품류(니스 분류) 결정이 보호 범위 결정', '국제 상표(마드리드 의정서)로 해외 동시 출원 가능'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 심판 ──────────────────────────────────────
    {
        'no': '67', 'tag': '특허 심판',
        'title': '거절결정불복심판 제기 전략',
        'summary': '심사 단계에서 최종 거절 결정을 받으면 3개월 이내에 특허심판원에 거절결정불복심판을 청구할 수 있습니다. 보정서와 의견서를 통해 새로운 주장을 추가할 수 있습니다.',
        'points': ['거절결정 확정 후 3개월 이내 청구 필수', '새로운 선행기술 자료 추가 제출 가능', '기각 시 특허법원·대법원으로 상소 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '68', 'tag': '특허 심판',
        'title': '정정심판으로 등록 특허의 흠결 치유하기',
        'summary': '등록된 특허에 오기, 불명확한 기재 등의 흠결이 있으면 정정심판으로 수정할 수 있습니다. 단, 청구범위를 실질적으로 확장하거나 변경하는 정정은 허용되지 않습니다.',
        'points': ['오기 정정, 불명확한 기재 해소 목적으로만 가능', '청구범위의 실질적 확장·변경 불가', '무효심판 진행 중에는 정정 심판과 병행 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '69', 'tag': '특허 심판',
        'title': '권리범위확인심판의 활용',
        'summary': '자신의 발명이 타인의 특허 권리범위에 속하는지 여부를 심판으로 확인받을 수 있습니다. 특허 분쟁 전 사전 확인 수단으로 활용되며, 적극적·소극적 두 가지 유형이 있습니다.',
        'points': ['소극적 확인심판: 내 기술이 침해에 해당 안 됨 확인', '적극적 확인심판: 상대 기술이 내 특허 범위 해당 확인', '심판 결과가 소송에 직접 구속력 없음에 주의'],
        'agent': None, 'agent_url': None,
    },

    # ── 연구소·대학 특허 ──────────────────────────────────────
    {
        'no': '70', 'tag': '연구소·대학 특허',
        'title': '정부 R&D 과제의 특허 귀속과 관리',
        'summary': '국가 R&D 과제로 개발된 발명은 특허법 및 국가연구개발혁신법에 따라 귀속 주체가 결정됩니다. 참여 기관과의 지분 공유, 정부 납부 의무 등을 사전에 확인해야 합니다.',
        'points': ['과제 협약서에 특허 귀속 조항 명시', '공동 소유 시 모든 공동 소유자의 동의 필요', '해외 출원 시 정부 승인 절차 확인'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '71', 'tag': '연구소·대학 특허',
        'title': '대학 기술이전(Technology Transfer) 절차',
        'summary': '대학 내 TLO(기술이전사무소)는 연구자의 발명을 특허화하고 기업에 이전하는 역할을 합니다. 발명신고서 제출부터 기술이전 계약까지의 절차를 이해하면 연구 성과를 효과적으로 사업화할 수 있습니다.',
        'points': ['발명신고서 제출 → 특허 출원 결정 → 출원 → 이전 협상', '기술료 수입은 발명자·대학 간 배분 규정 적용', 'NTIS, R&D 성과물 등록 시스템 활용'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 가치 평가 ──────────────────────────────────────
    {
        'no': '72', 'tag': '특허 가치 평가',
        'title': '특허 가치 평가의 3가지 접근법',
        'summary': '특허 가치는 비용 접근법, 시장 접근법, 수익 접근법으로 평가합니다. M&A·기술이전·담보 설정 등 목적에 따라 적합한 방법을 선택해야 합니다.',
        'points': ['비용 접근법: 발명·출원·유지 비용 합산', '시장 접근법: 유사 특허 거래 사례 비교', '수익 접근법: 미래 로열티 현재가치 환산(DCF)'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '73', 'tag': '특허 가치 평가',
        'title': 'IP 담보 대출 활용법',
        'summary': '보유 특허를 담보로 금융기관에서 대출을 받을 수 있습니다. 기술보증기금(기보), 신용보증기금(신보)의 IP 보증 프로그램을 활용하면 현금 유동성을 확보할 수 있습니다.',
        'points': ['기보 IP 보증 프로그램: 특허 가치 평가 후 보증 발급', '특허가치평가기관의 공인 평가 필요', '등록 특허 + 출원 중 특허 모두 대상 가능'],
        'agent': None, 'agent_url': None,
    },

    # ── IP 비용·지원 ──────────────────────────────────────
    {
        'no': '74', 'tag': 'IP 비용·지원',
        'title': '중소기업·스타트업이 받을 수 있는 특허 비용 지원',
        'summary': '특허청의 IP 나래 프로그램, 지역 지식재산센터 지원 사업, 기술보증기금의 IP 보증 등 다양한 공공 지원을 활용하면 특허 비용 부담을 크게 낮출 수 있습니다.',
        'points': ['IP 나래: 스타트업 대상 특허 비용 최대 80% 지원', '지역 지재권센터 무료 컨설팅·출원 지원', '해외 출원 바우처 사업으로 PCT 비용 절감'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '75', 'tag': 'IP 비용·지원',
        'title': '해외 특허 출원 비용 절감 전략',
        'summary': '해외 출원은 번역비, 대리인비, 관납료가 모두 발생해 국가당 500–2,000만원 이상 소요됩니다. PCT 출원으로 결정을 연기하고, 핵심 시장에만 집중 진입하는 전략이 비용 효율적입니다.',
        'points': ['PCT 국제 출원으로 30개월간 결정 유예', '핵심 시장 3–5개국 선택 집중 전략', 'PPH(특허심사하이웨이)로 심사 기간·비용 절감'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '76', 'tag': 'IP 비용·지원',
        'title': 'PPH(특허심사하이웨이) 제도로 해외 심사 가속화',
        'summary': '한 나라에서 특허 등록 결정을 받으면, 협력 국가에서 해당 심사 결과를 활용해 심사를 빠르게 진행할 수 있습니다. 한국은 미국·일본·중국·유럽 등 20개국 이상과 PPH 협정을 체결했습니다.',
        'points': ['국내 등록 결정 후 PPH 신청으로 해외 우선 심사', '심사 기간 평균 50–70% 단축', '비용은 일반 심사와 동일'],
        'agent': None, 'agent_url': None,
    },

    # ── 영업비밀 ──────────────────────────────────────
    {
        'no': '77', 'tag': '영업비밀',
        'title': '특허 vs 영업비밀: 언제 무엇을 선택할까?',
        'summary': '특허는 20년간 독점권을 주지만 기술이 공개됩니다. 영업비밀은 기간 제한 없이 비밀을 유지하는 한 보호되지만, 역엔지니어링·독자적 개발로 타인이 동일 기술을 취득하면 보호가 어렵습니다.',
        'points': ['제조 공정·배합 비율: 영업비밀이 유리', '제품 기능·인터페이스: 특허가 유리', '코카콜라 원액처럼 역엔지니어링 불가 기술은 영업비밀'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '78', 'tag': '영업비밀',
        'title': '영업비밀 보호 요건 3가지',
        'summary': '영업비밀로 보호받으려면 ① 비공지성(공개되지 않아야 함) ② 경제적 가치 ③ 비밀 관리성(비밀로 관리해야 함) 세 가지 요건을 모두 충족해야 합니다.',
        'points': ['비공지성: 불특정 다수에게 알려지지 않아야 함', '경제적 가치: 경쟁자에게 유용한 정보여야 함', '비밀 관리성: 접근 제한·보안 조치 운영 필수'],
        'agent': None, 'agent_url': None,
    },

    # ── 특허 동향 ──────────────────────────────────────
    {
        'no': '79', 'tag': '특허 동향',
        'title': '2025년 AI 특허 출원 급증 트렌드 분석',
        'summary': 'WIPO에 따르면 AI 관련 특허 출원은 2024년 대비 40% 이상 증가했습니다. 생성형 AI, 멀티모달 모델, 에이전트 AI 분야가 특히 두드러지며 한국·미국·중국이 상위를 차지합니다.',
        'points': ['생성형 AI: 텍스트·이미지·코드 생성 특허 폭증', '에이전트 AI: 멀티에이전트 협업 시스템 특허 증가', 'AI 반도체(NPU) 아키텍처 특허도 급성장'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '80', 'tag': '특허 동향',
        'title': '그린테크·친환경 특허의 부상',
        'summary': '탄소중립 목표와 ESG 경영 트렌드에 따라 수소 에너지, 탄소 포집(CCS), 배터리 재활용, 그린 암모니아 등 친환경 기술 분야의 특허 출원이 빠르게 증가하고 있습니다.',
        'points': ['수소 생산·저장·운반 특허 3배 이상 증가', 'CCUS(탄소 포집·활용·저장) 특허 수요 급증', '배터리 재활용·리유즈 공정 특허 공백 여전히 존재'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '81', 'tag': '특허 동향',
        'title': '양자 컴퓨팅 특허 경쟁 현황',
        'summary': 'IBM, Google, 국내 삼성·LG 등이 양자 컴퓨팅 하드웨어와 알고리즘 특허 포트폴리오를 구축 중입니다. 양자 오류 수정, 큐비트 제어, 양자 통신 암호 분야가 핵심입니다.',
        'points': ['양자 오류 수정 알고리즘 특허 경쟁 치열', '큐비트 제조·제어 방법이 핵심 원천 특허', '국내 정부 양자 특허 지원 사업 적극 활용 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '82', 'tag': '특허 동향',
        'title': 'WIPO AI 특허 가이드라인 2025 핵심 내용',
        'summary': 'WIPO는 2025년 AI 관련 특허 출원에 관한 국제 가이드라인을 발표했습니다. AI 보조 발명의 발명자 요건, 청구항 적격성 판단 기준, 공시 의무 등을 명확히 했습니다.',
        'points': ['AI 보조 발명 시 인간 기여도 명시 권장', '청구항 적격성: 기술적 효과 중심 판단', '각국 심사 지침 업데이트에 맞춘 전략 수정 필요'],
        'agent': None, 'agent_url': None,
    },

    # ── 실무 팁 ──────────────────────────────────────
    {
        'no': '83', 'tag': '실무 팁',
        'title': '변리사 선임 전 반드시 확인해야 할 사항',
        'summary': '변리사 선임은 특허의 질을 결정짓는 가장 중요한 요소 중 하나입니다. 해당 기술 분야 전문성, 과거 출원 실적, 청구항 작성 스타일을 검토하고 면담 후 선임해야 합니다.',
        'points': ['기술 분야별 전문 변리사 선임 권장', '동일 분야 최근 등록 사례 확인', '초안 검토 기회 및 소통 방식 사전 확인'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '84', 'tag': '실무 팁',
        'title': '발명 노트(Lab Notebook) 작성과 관리',
        'summary': '발명 완성 과정을 날짜와 함께 기록한 발명 노트는 분쟁 시 선발명 입증 자료로 활용됩니다. 디지털 발명 노트 도구를 활용해 타임스탬프를 확보하는 것이 좋습니다.',
        'points': ['날짜·서명·증인 서명이 있는 발명 노트 유지', '디지털 도구(Notarize, IP Note) 활용 권장', '주요 실험 데이터·도면 함께 보관'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '85', 'tag': '실무 팁',
        'title': '특허 명세서 AI 초안 도구 활용법',
        'summary': 'GPT-4, Claude 등 LLM 기반 도구를 활용하면 특허 명세서 초안 작성 시간을 80% 이상 단축할 수 있습니다. 단, AI 초안은 반드시 전문가 검토를 거쳐야 법적 효력을 갖는 완성본이 됩니다.',
        'points': ['발명 핵심 데이터 입력 후 초안 생성', '생성된 초안에서 기술적 오류·과장 표현 제거', '청구항 범위 최종 조정은 변리사와 협의'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '86', 'tag': '실무 팁',
        'title': '특허 출원서류 제출 전 최종 체크리스트',
        'summary': '출원 전 발명자 정보, 청구항 번호 연속성, 참조부호 일치 여부, 요약서 분량 등을 체크리스트로 확인하면 보정 명령 없이 통과 확률이 크게 높아집니다.',
        'points': ['발명자명·주소 정확성 확인', '청구항 번호 1번부터 연속 부여', '도면 참조부호와 명세서 참조부호 일치'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '87', 'tag': '실무 팁',
        'title': '특허 분석 무료 툴 TOP 5',
        'summary': 'KIPRIS, Google Patents, Espacenet, Patentscope(WIPO), Lens.org는 무료로 활용할 수 있는 강력한 특허 분석 도구입니다. 각각의 강점이 달라 목적에 맞게 조합해 사용하는 것이 효과적입니다.',
        'points': ['KIPRIS: 국내 특허 심층 검색', 'Google Patents: AI 번역·유사 특허 추천', 'Lens.org: 학술 논문과 특허 통합 분석'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '88', 'tag': '실무 팁',
        'title': 'IPC 분류코드 체계 이해하기',
        'summary': 'IPC(국제특허분류)는 기술 분야를 체계적으로 분류한 코드 체계입니다. 출원 시 적절한 IPC 코드를 부여하면 심사관 배정이 최적화되고 선행기술 조사 정확도가 높아집니다.',
        'points': ['IPC 코드: 섹션(A–H) → 클래스 → 서브클래스 → 그룹', '기술 분야별 핵심 IPC 코드 파악 필수', 'CPC(협력특허분류)는 IPC보다 더 세부적인 분류'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '89', 'tag': '실무 팁',
        'title': '출원 전 공개(Pre-Filing Disclosure) 리스크 관리',
        'summary': '학회 발표, 논문 투고, 투자자 미팅 등에서 발명을 공개하면 신규성이 상실될 수 있습니다. 공개 전 NDA 체결 또는 출원 후 공개 원칙을 엄격히 적용해야 합니다.',
        'points': ['학회 발표 전 반드시 가출원 또는 출원 완료', '투자자 NDA 체결 후 기술 공개', '온라인 게시·SNS 공개도 신규성 상실 원인'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '90', 'tag': '실무 팁',
        'title': '특허 만료 전 존속기간 연장 제도',
        'summary': '의약품·농약 특허는 허가 심사 기간만큼 존속기간을 최대 5년 연장할 수 있습니다. 의약품 허가 취득 후 3개월 이내에 연장 등록 출원을 해야 합니다.',
        'points': ['의약품·농약 특허: 허가 심사 기간만큼 연장 가능', '최대 연장 기간: 5년', '허가 취득 후 3개월 이내 신청 필수'],
        'agent': None, 'agent_url': None,
    },

    # ── PYPI 서비스 ──────────────────────────────────────
    {
        'no': '91', 'tag': 'PYPI 서비스',
        'title': 'PYPI AI 파이프라인으로 명세서 완성까지 걸리는 시간',
        'summary': 'PYPI의 AI 특허 파이프라인은 발명 데이터 입력 후 AI 상담 → 청구항 생성 → 도면 작성 → 명세서 완성까지 평균 30분 이내에 초안을 완성합니다. 변리사 검토 시간을 80% 이상 절감합니다.',
        'points': ['발명 데이터 입력 후 AI 분석 약 2분', '청구항 초안 자동 생성 약 5분', '명세서 전체 초안 완성 약 20–30분'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '92', 'tag': 'PYPI 서비스',
        'title': 'PYPI의 멀티 에이전트 품질 검수 시스템',
        'summary': 'PYPI는 생성된 명세서를 Master Agent가 1차 작성하고, Critic Agent가 신규성·진보성·기재불비 관점에서 검수하는 이중 검증 구조를 채택합니다. 이를 통해 인간 변리사 수준의 품질을 달성합니다.',
        'points': ['Master Agent: 발명 분석 및 초안 생성', 'Critic Agent: 품질 기준 대비 자동 검수', '품질 점수 80점 이상 시 최종 출력'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '93', 'tag': 'PYPI 서비스',
        'title': 'AI 특허 초안의 한계와 전문가 검토의 중요성',
        'summary': 'AI가 생성한 특허 초안은 속도와 비용 면에서 탁월하지만, 최신 판례·심사 기준 반영, 법적 책임 있는 의견 제시는 사람 변리사의 영역입니다. PYPI 초안을 기반으로 전문가 검토를 거치는 하이브리드 방식이 최선입니다.',
        'points': ['AI 초안 생성 후 변리사 최종 검토 권장', '심사관 경향·최신 판례는 전문가만이 반영 가능', 'PYPI + 변리사 협업으로 비용·시간 최적화'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '94', 'tag': 'PYPI 서비스',
        'title': 'PYPI 도면 에이전트로 특허 도면 자동 생성하기',
        'summary': 'PYPI의 도면 에이전트는 명세서 내용을 분석해 흐름도, 블록도, 구성도 등을 자동으로 생성합니다. KIPO 규격에 맞게 참조부호와 도면 번호가 자동으로 부여됩니다.',
        'points': ['명세서 텍스트 → 도면 자동 변환', 'KIPO 규격(흑백 선도, 참조부호) 자동 준수', '흐름도·블록도·계층도 3가지 유형 지원'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '95', 'tag': 'PYPI 서비스',
        'title': 'PYPI 프로젝트 관리 기능 활용 가이드',
        'summary': 'PYPI의 워크스테이션에서 프로젝트별로 발명 데이터, AI 상담 내역, 청구항 초안, 명세서를 통합 관리할 수 있습니다. 여러 발명을 동시에 진행하며 진행 상황을 한눈에 파악할 수 있습니다.',
        'points': ['프로젝트별 발명 데이터·대화 내역 분리 관리', '파이프라인 진행도 실시간 확인', '청구항 직접 수정·저장 기능 지원'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '96', 'tag': 'PYPI 서비스',
        'title': 'PYPI 리포트로 완성되는 특허 명세서 초안',
        'summary': 'PYPI의 리포트 기능은 AI가 생성한 청구항, 명세서, 도면을 하나의 문서로 통합 출력합니다. PDF로 다운로드해 변리사에게 검토 의뢰하거나 직접 KIPO에 제출하는 참고 자료로 활용할 수 있습니다.',
        'points': ['청구항 + 발명의 설명 + 도면 통합 리포트', 'PDF 다운로드로 오프라인 활용 가능', '변리사 검토 의뢰용 초안으로 최적화'],
        'agent': None, 'agent_url': None,
    },

    # ── 기타 ──────────────────────────────────────
    {
        'no': '97', 'tag': '기타 IP',
        'title': '실용신안과 특허의 차이점',
        'summary': '실용신안은 물품의 형상·구조·조합에 관한 고안을 보호하며, 무심사 등록제로 빠르게 등록됩니다. 존속기간이 10년으로 특허보다 짧지만 초기 비용이 적고 등록이 빠릅니다.',
        'points': ['실용신안: 물품 형상·구조에 한정, 10년 보호', '무심사 등록으로 출원 후 1–2개월 내 등록', '기술적 수준이 낮은 창작도 보호 가능'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '98', 'tag': '기타 IP',
        'title': '저작권으로 보호받는 기술 콘텐츠의 범위',
        'summary': '기술 논문, API 문서, 코드 주석, 사용자 매뉴얼 등은 저작권으로 보호됩니다. 특허가 없어도 저작권 침해 주장이 가능하므로, IP 보호 전략에서 저작권을 함께 고려해야 합니다.',
        'points': ['창작성 있는 기술 문서·코드는 자동으로 저작권 발생', '등록 없이도 보호되지만 등록하면 침해 구제 유리', 'API 스펙 문서도 저작권 보호 대상'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '99', 'tag': 'IP 용어',
        'title': '특허 실무자가 꼭 알아야 할 IP 용어 30선',
        'summary': '특허 업무를 처음 접하면 생소한 용어가 많습니다. 신규성, 진보성, 명세서, 청구항, 선행기술, 거절이유통지, 우선권, 분할출원 등 핵심 용어를 이해하면 실무 소통이 원활해집니다.',
        'points': ['신규성(Novelty): 출원 전 공개되지 않은 새로움', '진보성(Inventive Step): 전문가가 쉽게 생각 못하는 창작성', '독립항(Independent Claim): 다른 항을 인용하지 않는 청구항'],
        'agent': None, 'agent_url': None,
    },
    {
        'no': '100', 'tag': 'IP 용어',
        'title': '특허 심사 단계별 핵심 용어 정리',
        'summary': '방식심사, 실체심사, 거절이유통지(OA), 의견서, 보정서, 등록결정, 거절결정, 심판청구까지 출원부터 등록까지의 각 단계에서 사용되는 용어를 정확히 이해하면 대응 전략 수립이 쉬워집니다.',
        'points': ['방식심사: 형식 요건(출원서류 완비 여부) 검토', '실체심사: 신규성·진보성·기재불비 심사', 'OA(Office Action): 거절이유 통지 — 2개월 내 응답 필수'],
        'agent': None, 'agent_url': None,
    },
]

def insights_view(request):
    return render(request, 'pages/insights.html', {'cards': _PATENT_INSIGHTS})


_QNA_DATA = [
    {
        'id': 'basics',
        'section': '출원 기초',
        'en': 'Patent Application Basics',
        'items': [
            ('특허란 무엇인가요?', '특허는 발명자가 일정 기간 독점적으로 발명을 실시할 수 있는 권리입니다. 한국에서는 특허청에 출원하여 심사를 거친 후 등록되며, 존속기간은 출원일로부터 20년입니다.'),
            ('특허 출원 절차는 어떻게 되나요?', '① 출원서 작성 → ② 특허청 제출 → ③ 방식심사 → ④ 출원공개(18개월) → ⑤ 실체심사 청구 → ⑥ 심사 → ⑦ 등록결정 또는 거절결정 순으로 진행됩니다.'),
            ('특허 출원 비용은 얼마인가요?', '기본 출원료는 약 4만 6천 원(전자출원 기준)이며, 심사청구료, 등록료 등이 별도로 발생합니다. 중소기업·개인 발명자는 감면 혜택을 받을 수 있습니다.'),
            ('국내 우선권 주장이란 무엇인가요?', '먼저 출원한 특허를 기초로 1년 이내에 개량 발명을 포함한 새로운 출원을 하면서 선출원의 출원일을 우선일로 인정받는 제도입니다.'),
            ('PCT 국제출원이란?', 'Patent Cooperation Treaty(특허협력조약)에 따라 하나의 출원으로 160여 개 국가에 동시에 출원한 효과를 내는 제도입니다. 우선일로부터 30개월 이내에 각국 국내 단계로 진입해야 합니다.'),
            ('특허를 출원하면 바로 보호받나요?', '출원 즉시 출원 중(patent pending) 상태가 되어 일정 보호를 받습니다. 완전한 독점 실시권은 등록 후에 발생하며, 출원공개 후에는 보상금청구권이 생깁니다.'),
            ('비밀유지 기간은 얼마나 되나요?', '특허 출원 후 18개월이 경과하면 자동으로 공개됩니다. 비밀 유지를 원하면 출원공개 전에 취하하거나 비밀 취급 신청을 해야 합니다.'),
            ('선출원주의와 선발명주의의 차이는?', '한국·일본·유럽 등 대부분 국가는 먼저 출원한 자에게 권리를 주는 선출원주의를 채택합니다. 미국도 2013년부터 선출원주의로 전환했습니다.'),
        ],
    },
    {
        'id': 'claims',
        'section': '청구항 작성',
        'en': 'Writing Claims',
        'items': [
            ('청구항이란 무엇인가요?', '특허 보호 범위를 법적으로 정의하는 핵심 문서입니다. 청구항에 기재된 구성요소 전체를 포함하는 제품·방법에만 특허권이 미치므로, 권리 범위를 넓게 작성하는 것이 중요합니다.'),
            ('독립항과 종속항의 차이는?', '독립항은 다른 청구항을 인용하지 않고 자체적으로 완결된 청구항이며, 종속항은 독립항 또는 다른 종속항을 인용하여 추가 한정 사항을 더한 청구항입니다.'),
            ('청구항 작성 시 가장 중요한 원칙은?', '① 명확성: 구성요소를 명확하게 기재, ② 간결성: 불필요한 한정을 피해 권리 범위를 넓게, ③ 뒷받침: 명세서 실시예와 일치해야 합니다.'),
            ('PYPI가 청구항 작성을 어떻게 도와주나요?', 'PYPI 청구항 에이전트(Agent IV)는 발명의 구성요소를 분석하여 독립항과 종속항을 자동 생성하고, 선행기술 조사 결과를 반영하여 신규성·진보성 확보 전략을 제안합니다.'),
            ('균등론이란 무엇인가요?', '청구항 문언에는 포함되지 않지만 실질적으로 동일한 수단·기능·결과를 가지는 침해에도 특허권이 미친다는 법리입니다. 청구항 작성 시 균등론 적용 가능성을 고려해야 합니다.'),
            ('방법 청구항과 물건 청구항의 차이는?', '물건 청구항은 제품·장치·시스템 등 물적 대상을, 방법 청구항은 특정 순서의 단계를 보호합니다. 동일 발명이라도 두 유형 모두 출원하면 보호 범위가 넓어집니다.'),
            ('기능식 청구항이란?', '"~하기 위한 수단(means for)"처럼 기능으로 구성요소를 특정하는 청구항입니다. 명세서에 대응 구조가 명확히 기재되어야 하며, 해석 범위가 달라질 수 있습니다.'),
            ('청구항에 실시예를 모두 기재해야 하나요?', '아닙니다. 청구항은 보호받고자 하는 범위를 정의하며, 실시예는 명세서 본문에 기재합니다. 청구항이 지나치게 좁으면 경쟁사가 쉽게 우회할 수 있습니다.'),
        ],
    },
    {
        'id': 'exam',
        'section': '심사·등록',
        'en': 'Examination & Registration',
        'items': [
            ('실체심사는 언제 청구해야 하나요?', '출원일로부터 3년 이내에 심사청구를 해야 합니다. 기간 내 청구하지 않으면 출원이 취하 간주됩니다. 조기 심사를 원하면 우선심사 신청도 가능합니다.'),
            ('신규성 요건이란?', '출원일 전에 동일한 발명이 공개·공지·공용되지 않아야 합니다. 발명자 본인이 먼저 발표한 경우에도 신규성이 문제될 수 있으나, 공지 후 12개월 이내 출원 시 신규성 예외 규정이 적용됩니다.'),
            ('진보성이란 무엇인가요?', '선행기술로부터 그 발명이 속하는 기술 분야의 통상의 지식을 가진 자(통상의 기술자)가 쉽게 발명할 수 없어야 합니다. 특허 거절의 가장 흔한 이유입니다.'),
            ('거절이유 통지를 받았을 때 어떻게 해야 하나요?', '심사관의 거절이유 통지에 대해 의견서와 보정서를 제출하여 대응합니다. 청구항 범위를 좁히거나 선행기술과의 차이점을 설명함으로써 등록 가능성을 높일 수 있습니다.'),
            ('특허 심사 기간은 얼마나 걸리나요?', '일반 심사는 평균 약 14~18개월, 우선심사를 이용하면 약 3~6개월 내에 결과를 받을 수 있습니다. 분야별·시기별로 차이가 있습니다.'),
            ('분할출원이란?', '하나의 출원에 여러 발명이 포함된 경우, 또는 거절된 부분을 별도로 권리화하고 싶을 때 원출원의 일부를 분리하여 새로운 출원으로 하는 것입니다. 원출원의 출원일을 유지합니다.'),
            ('특허 등록 후 관리는 어떻게 하나요?', '매년 등록료(연차료)를 납부해야 권리가 유지됩니다. 4~6년차 기준 약 3만~4만 원, 이후 점차 증가합니다. 미납 시 특허권이 소멸됩니다.'),
            ('특허 무효심판이란?', '등록된 특허에 무효 사유가 있을 때 누구든지 특허심판원에 무효를 구하는 심판입니다. 신규성·진보성 결여, 명세서 기재 불비 등이 주요 무효 사유입니다.'),
        ],
    },
    {
        'id': 'ai',
        'section': 'AI 특허 Q&A',
        'en': 'AI & Patent Law',
        'items': [
            ('AI가 발명한 것도 특허를 받을 수 있나요?', '현재 대부분 국가에서 발명자는 자연인(사람)이어야 합니다. AI가 발명에 기여했더라도 이를 지도한 인간 개발자가 발명자로 기재됩니다. 다만 AI 발명자 인정 여부에 대한 국제적 논의가 활발히 진행 중입니다.'),
            ('AI가 생성한 명세서의 특허 출원이 가능한가요?', 'AI 도구로 작성된 명세서도 발명의 기술적 내용이 충분히 뒷받침된다면 출원 가능합니다. PYPI처럼 AI가 초안을 작성하고 발명자·변리사가 검토·수정하는 방식이 현재 실무에서 가장 안전합니다.'),
            ('기계학습 모델 자체를 특허로 보호할 수 있나요?', '모델 아키텍처, 학습 방법, 특정 응용(의료 진단 AI 등)은 특허 가능합니다. 단순 수학적 알고리즘이나 추상적 아이디어는 특허 대상이 되지 않으므로, 기술적 문제 해결에 초점을 맞춰 청구항을 작성해야 합니다.'),
            ('AI 특허 출원이 증가하고 있나요?', '네, 급격히 증가하고 있습니다. 한국 특허청 기준으로 AI 관련 특허 출원은 최근 5년간 연평균 30% 이상 성장했습니다. 삼성전자, 네이버, 카카오, ETRI 등이 주요 출원인입니다.'),
            ('PYPI를 사용하면 특허 출원까지 자동으로 되나요?', 'PYPI는 특허 명세서 초안(청구항·도면·발명의 설명 등)을 AI로 자동 생성하여 시간을 대폭 단축합니다. 최종 출원은 등록 변리사 검토 후 진행하는 것을 권장하며, 이는 현행 변리사법 요건을 충족합니다.'),
            ('AI 특허 출원 시 영업비밀과의 선택은?', 'AI 모델의 핵심 가중치·학습 데이터는 특허 출원 시 공개됩니다. 공개를 원치 않는다면 영업비밀로 보호하는 것이 나을 수 있습니다. 둘 중 무엇이 유리한지는 발명의 성격과 경쟁 환경에 따라 다릅니다.'),
            ('생성형 AI 출력물의 저작권·특허는 누구에게?', '저작권법상 AI가 생성한 결과물의 저작자는 원칙상 AI를 활용한 인간 사용자입니다. 특허법상 발명자도 AI를 도구로 활용한 사람이 됩니다. 다만 자동화 정도가 높을수록 법적 불확실성이 커집니다.'),
            ('PYPI 도면 에이전트가 생성한 도면의 권리는?', 'PYPI가 생성한 SVG 도면은 발명자가 특허 출원에 활용할 수 있으며, 해당 도면이 포함된 특허권은 출원인(발명자 또는 법인)에게 귀속됩니다. PYPI는 도구로서 권리를 주장하지 않습니다.'),
        ],
    },
]


def qna_view(request):
    total = sum(len(s['items']) for s in _QNA_DATA)
    return render(request, 'pages/qna.html', {'qna_sections': _QNA_DATA, 'total_count': total})


_PIPELINE_ORDER = [
    ('summary', _AGENT_PAGES['summary']),
    ('prior-art', _AGENT_PAGES['prior-art']),
    ('claim', _AGENT_PAGES['claim']),
    ('drawing', _AGENT_PAGES['drawing']),
    ('specification', _AGENT_PAGES['specification']),
    ('composer', _AGENT_PAGES['composer']),
]

def _build_gallery():
    # SVG 파일 16개 각각 1:1 매핑 — 중복 없음
    return [
        # ── 기계 (mech_a / mech_b / mech_c) ─────────────────────────
        {
            'num': 'DWG-001', 'cat': '기계',
            'svg_type': 'mech_a', 'svg_url': '/static/svgs/gallery/mech_a.svg',
            'name': '유성기어 감속기 어셈블리',
            'pno': 'KR10-2021-0087432', 'assignee': '현대자동차㈜',
            'ipc': 'F16H 1/28', 'year': 2021, 'fig': 'FIG.1 정면 단면도',
            'desc': '링기어·유성기어·선기어의 배치와 동력 전달 경로를 나타낸 고토크 유성기어 감속기 정면 단면 구조도.',
        },
        {
            'num': 'DWG-002', 'cat': '기계',
            'svg_type': 'mech_b', 'svg_url': '/static/svgs/gallery/mech_b.svg',
            'name': '이중 피스톤 유압 실린더',
            'pno': 'KR10-2020-0134521', 'assignee': '두산인프라코어㈜',
            'ipc': 'F15B 15/14', 'year': 2020, 'fig': 'FIG.2 단면도',
            'desc': '직선 왕복 운동용 이중 피스톤 유압 실린더의 내부 실링 구조와 포트 배치를 나타낸 단면도.',
        },
        {
            'num': 'DWG-003', 'cat': '기계',
            'svg_type': 'mech_c', 'svg_url': '/static/svgs/gallery/mech_c.svg',
            'name': '앵귤러 콘택트 볼베어링',
            'pno': 'US10,934,812 B2', 'assignee': 'Samsung SDI Co., Ltd.',
            'ipc': 'F16C 33/58', 'year': 2021, 'fig': 'FIG.3 단면 상세도',
            'desc': '고속 주축 적용을 위한 앵귤러 콘택트 볼베어링의 내·외륜, 볼 배열 및 오일 공급 홈 구조 상세도.',
        },
        # ── 전자·회로 (circuit_a / circuit_b) ─────────────────────────
        {
            'num': 'DWG-004', 'cat': '전자·회로',
            'svg_type': 'circuit_a', 'svg_url': '/static/svgs/gallery/circuit_a.svg',
            'name': '3상 풀브릿지 인버터 회로',
            'pno': 'KR10-2021-0034521', 'assignee': '삼성전자㈜',
            'ipc': 'H02M 7/48', 'year': 2021, 'fig': 'FIG.1 회로도',
            'desc': 'IGBT 기반 3상 풀브릿지 인버터의 스위칭 소자 배치, 게이트 드라이버 연결 및 DC 링크 커패시터 구성 회로도.',
        },
        {
            'num': 'DWG-005', 'cat': '전자·회로',
            'svg_type': 'circuit_b', 'svg_url': '/static/svgs/gallery/circuit_b.svg',
            'name': 'PLL 위상 고정 루프 회로',
            'pno': 'US10,979,055 B2', 'assignee': 'Samsung Electronics Co., Ltd.',
            'ipc': 'H03L 7/089', 'year': 2021, 'fig': 'FIG.3 블록 회로도',
            'desc': '위상 검출기·루프 필터·VCO·분주기로 구성된 PLL 주파수 합성 경로와 피드백 루프 세부 블록 회로도.',
        },
        # ── 소프트웨어 블록도 (block_a / block_b / block_c) ───────────
        {
            'num': 'DWG-006', 'cat': '소프트웨어',
            'svg_type': 'block_a', 'svg_url': '/static/svgs/gallery/block_a.svg',
            'name': '특허 AI 멀티에이전트 파이프라인',
            'pno': 'KR10-2023-0056789', 'assignee': 'PYPI Inc.',
            'ipc': 'G06N 3/08', 'year': 2023, 'fig': 'FIG.1 시스템 구성도',
            'desc': '상담→요약→선행기술→청구항→도면→명세서→컴포저 7단계 AI 에이전트가 LangGraph SharedState로 연결되는 파이프라인 구성도.',
        },
        {
            'num': 'DWG-007', 'cat': '소프트웨어',
            'svg_type': 'block_b', 'svg_url': '/static/svgs/gallery/block_b.svg',
            'name': '분산 마이크로서비스 아키텍처',
            'pno': 'KR10-2022-0134012', 'assignee': '네이버㈜',
            'ipc': 'G06F 9/50', 'year': 2022, 'fig': 'FIG.2 시스템 구성도',
            'desc': 'API 게이트웨이·서비스 메시·컨테이너 오케스트레이션으로 구성된 마이크로서비스 간 통신 및 로드밸런싱 시스템 구성도.',
        },
        {
            'num': 'DWG-008', 'cat': '소프트웨어',
            'svg_type': 'block_c', 'svg_url': '/static/svgs/gallery/block_c.svg',
            'name': 'LLM 프롬프트 최적화 시스템',
            'pno': 'KR10-2023-0089012', 'assignee': '네이버클라우드㈜',
            'ipc': 'G06N 20/00', 'year': 2023, 'fig': 'FIG.2 시스템 구성도',
            'desc': 'RAG 컨텍스트 검색·Chain-of-Thought 프롬프트 생성·응답 품질 평가 모듈이 연동되는 LLM 최적화 파이프라인 구성도.',
        },
        # ── 소프트웨어 흐름도 (flow_a / flow_b) ───────────────────────
        {
            'num': 'DWG-009', 'cat': '소프트웨어',
            'svg_type': 'flow_a', 'svg_url': '/static/svgs/gallery/flow_a.svg',
            'name': 'AI 기반 특허 자동 분류 흐름도',
            'pno': 'KR10-2023-0023456', 'assignee': '카카오㈜',
            'ipc': 'G06F 11/36', 'year': 2023, 'fig': 'FIG.3 흐름도',
            'desc': '특허 텍스트 입력→임베딩 벡터화→IPC 분류 추론→신뢰도 검증→출력까지의 AI 특허 자동 분류 처리 흐름도.',
        },
        {
            'num': 'DWG-010', 'cat': '소프트웨어',
            'svg_type': 'flow_b', 'svg_url': '/static/svgs/gallery/flow_b.svg',
            'name': '실시간 데이터 스트리밍 파이프라인',
            'pno': 'US11,372,879 B2', 'assignee': 'Coupang Corp.',
            'ipc': 'G06F 16/903', 'year': 2022, 'fig': 'FIG.1 처리 흐름도',
            'desc': 'Kafka 이벤트 버스→스트림 처리 엔진→실시간 집계→데이터 레이크 적재 및 백프레셔 제어 분기를 포함한 처리 흐름도.',
        },
        # ── 바이오·의료 (bio_a / bio_b) ───────────────────────────────
        {
            'num': 'DWG-011', 'cat': '바이오·의료',
            'svg_type': 'bio_a', 'svg_url': '/static/svgs/gallery/bio_a.svg',
            'name': '단일세포 유전체 분석 플로우셀',
            'pno': 'KR10-2021-0112678', 'assignee': '포항공과대학교 기술지주㈜',
            'ipc': 'G01N 15/14', 'year': 2021, 'fig': 'FIG.2 단면도 · 평면도',
            'desc': '마이크로채널 내 단일세포 포획→용해→핵산 추출을 수행하는 랩온칩 플로우셀의 채널 기하학 및 전극 배치 단면 구조도.',
        },
        {
            'num': 'DWG-012', 'cat': '바이오·의료',
            'svg_type': 'bio_b', 'svg_url': '/static/svgs/gallery/bio_b.svg',
            'name': 'CRISPR-Cas9 나노입자 전달 시스템',
            'pno': 'KR10-2021-0145234', 'assignee': '한미약품㈜',
            'ipc': 'A61K 9/51', 'year': 2021, 'fig': 'FIG.4 단면 작동도',
            'desc': 'CRISPR-Cas9 RNP를 지질 나노입자에 캡슐화하여 표적 세포에 전달하는 엔도솜 탈출 메커니즘과 핵 전달 경로 작동도.',
        },
        # ── 화학·공정 (chem_a / chem_b) ───────────────────────────────
        {
            'num': 'DWG-013', 'cat': '화학·공정',
            'svg_type': 'chem_a', 'svg_url': '/static/svgs/gallery/chem_a.svg',
            'name': '연속흐름 마이크로 반응기',
            'pno': 'EP3,889,134 A1', 'assignee': '한화솔루션㈜',
            'ipc': 'B01J 19/12', 'year': 2021, 'fig': 'FIG.2 단면 채널 상세도',
            'desc': '열교환 채널과 반응 채널이 교대 배열된 마이크로 반응기의 유체 혼합 경로, 온도 제어 구조 및 포트 배치 단면 상세도.',
        },
        {
            'num': 'DWG-014', 'cat': '화학·공정',
            'svg_type': 'chem_b', 'svg_url': '/static/svgs/gallery/chem_b.svg',
            'name': '나권형 역삼투 분리막 모듈',
            'pno': 'KR10-2022-0101234', 'assignee': '코오롱인더스트리㈜',
            'ipc': 'B01D 65/00', 'year': 2022, 'fig': 'FIG.1 단면도',
            'desc': '나권형 역삼투 분리막 엘리먼트의 막 적층 구조, 투과수 채널, 급수·농축수 흐름 경로 단면 구조도.',
        },
        # ── 구조·건축 (struct_a / struct_b) ───────────────────────────
        {
            'num': 'DWG-015', 'cat': '구조·건축',
            'svg_type': 'struct_a', 'svg_url': '/static/svgs/gallery/struct_a.svg',
            'name': '납심형 탄성받침 면진 장치',
            'pno': 'KR10-2023-0212456', 'assignee': '현대건설㈜',
            'ipc': 'E04H 9/02', 'year': 2023, 'fig': 'FIG.2 단면 상세도',
            'desc': '내부 고무층과 강판이 교대 적층된 납심형 탄성받침의 면진 성능·수직 지지력·납심 에너지 흡수 메커니즘 단면 상세도.',
        },
        {
            'num': 'DWG-016', 'cat': '구조·건축',
            'svg_type': 'struct_b', 'svg_url': '/static/svgs/gallery/struct_b.svg',
            'name': '프리스트레스트 콘크리트 슬래브보',
            'pno': 'KR10-2023-0056678', 'assignee': '현대건설㈜',
            'ipc': 'E04C 3/20', 'year': 2023, 'fig': 'FIG.1 단면 배근도',
            'desc': 'PS 강선 배치·긴장 정착 상세·전단 스터럽 배근 및 프리스트레스 손실 보상 설계를 포함한 프리텐션 슬래브보 단면 배근도.',
        },
    ]

def _build_gallery_UNUSED():
    cats = [
        ('기계', [
            ('KR10-2021-0087432','현대자동차㈜','F16H 1/04',2021,'기어 어셈블리 메커니즘','FIG.1 정면도'),
            ('KR10-2020-0134521','두산인프라코어','F15B 15/14',2020,'이중 피스톤 유압 실린더','FIG.2 단면도'),
            ('US10,934,812 B2','Samsung SDI','F16C 33/58',2021,'볼 베어링 내륜 구조체','FIG.3 정면도'),
            ('KR10-2022-0045678','LS Electric','F16H 27/02',2022,'캠 구동 래칫 장치','FIG.1 측면도'),
            ('EP3,812,611 A1','HD현대','F16H 1/28',2021,'고토크 유성기어 감속기','FIG.2 단면도'),
            ('KR10-2019-0112345','포스코','F16H 7/06',2019,'다단 체인 드라이브','FIG.1 평면도'),
            ('JP2021-183412 A','효성중공업','F16H 1/12',2021,'웜기어 자동 감속 모듈','FIG.3 블록도'),
            ('KR10-2023-0056789','삼성중공업','F16H 55/17',2023,'헬리컬 기어 소음 저감','FIG.1 정면도'),
            ('US11,187,303 B2','한화에어로스페이스','F16H 1/14',2021,'베벨 기어 동력 전달','FIG.4 정면도'),
            ('KR10-2022-0078901','현대트랜시스','F16H 1/32',2022,'플래닛 기어 세트','FIG.2 단면도'),
            ('EP3,754,210 B1','만도','F16D 13/64',2021,'클러치 디스크 마찰 저감','FIG.1 상세도'),
            ('KR10-2020-0098765','현대모비스','F16D 65/22',2020,'드럼 브레이크 자동 조정','FIG.3 단면도'),
            ('KR10-2021-0023456','현대자동차㈜','F16C 7/02',2021,'커넥팅 로드 경량화','FIG.1 정면도'),
            ('US10,989,241 B2','GM Korea','F16F 15/26',2021,'크랭크샤프트 밸런싱','FIG.2 측면도'),
            ('EP3,693,548 A1','두산에너빌리티','F01D 5/18',2020,'터빈 블레이드 냉각','FIG.5 단면도'),
            ('KR10-2022-0134567','KSB코리아','F04D 29/18',2022,'원심형 펌프 임펠러','FIG.1 평면도'),
            ('JP2022-145632 A','LG전자','F04C 18/02',2022,'스크롤 압축기 구동부','FIG.2 단면도'),
            ('KR10-2020-0067890','한화파워시스템','F04B 39/10',2020,'왕복동 압축기 밸브','FIG.3 상세도'),
            ('EP3,832,147 A1','파커한니핀코리아','F01C 1/344',2021,'로터리 베인 모터','FIG.1 정면도'),
            ('KR10-2023-0012345','SMC코리아','F15B 11/042',2023,'리니어 액추에이터','FIG.2 블록도'),
            ('US11,035,364 B2','시노팩스코리아','F04D 13/02',2021,'마그네틱 커플링 펌프','FIG.1 단면도'),
            ('KR10-2021-0056789','삼양밸브','F16K 41/10',2021,'벨로우즈 실링 밸브','FIG.3 측면도'),
            ('EP3,875,221 A1','SMC코리아','B25J 15/08',2021,'공압 그리퍼 메커니즘','FIG.1 정면도'),
            ('KR10-2022-0089012','THK코리아','F16H 25/22',2022,'볼 스크류 선형 구동','FIG.2 단면도'),
            ('JP2021-176543 A','게이츠코리아','F16H 7/02',2021,'타이밍 벨트 풀리','FIG.1 정면도'),
            ('KR10-2023-0067890','현대위아','G01L 3/10',2023,'토크 센서 드라이브샤프트','FIG.3 상세도'),
            ('US11,260,487 B2','성림첨단산업','B23G 1/02',2022,'나사산 정밀 연삭 가이드','FIG.2 단면도'),
            ('KR10-2021-0101234','한미반도체','B25J 15/06',2021,'진공 흡착 핸들링 장치','FIG.1 평면도'),
            ('EP3,900,862 B1','화천기계','B23Q 5/04',2022,'5축 가공 센터 스핀들','FIG.2 단면도'),
            ('KR10-2020-0145678','삼정밸런스','F16C 33/46',2020,'롤러 베어링 케이지','FIG.4 상세도'),
            ('KR10-2022-0012678','현대제철','B21D 26/033',2022,'하이드로포밍 금형','FIG.1 단면도'),
            ('KR10-2023-0089012','현대자동차㈜','B21D 43/02',2023,'프레스 소재 공급 장치','FIG.2 평면도'),
            ('EP3,982,517 A1','현대엘리베이터','B60L 13/04',2022,'자기부상 이송 시스템','FIG.4 블록도'),
            ('KR10-2021-0112345','트럼프코리아','B23K 26/14',2021,'레이저 절단 정밀 가이드','FIG.1 단면도'),
            ('KR10-2019-0134567','포스코','B22D 11/053',2019,'연속주조 몰드 진동장치','FIG.3 측면도'),
            ('US11,154,946 B2','에머슨코리아','B23K 20/10',2021,'초음파 용접 혼 구조','FIG.2 정면도'),
            ('KR10-2022-0056012','에이스침대','F16F 1/36',2022,'방진 마운트 복합 구조','FIG.1 단면도'),
            ('KR10-2021-0078123','삼성전자㈜','B82Y 10/00',2021,'나노임프린트 스탬프','FIG.3 상세도'),
            ('JP2023-012345 A','마키노코리아','B23Q 7/14',2023,'자동 팔레트 교환 시스템','FIG.2 평면도'),
            ('KR10-2020-0189012','화천기계','B23Q 16/02',2020,'정밀 회전 인덱싱 테이블','FIG.1 단면도'),
            ('EP3,856,991 B1','삼성중공업','F16K 25/00',2021,'극저온 밸브 시트 구조','FIG.4 상세도'),
            ('KR10-2021-0034521','LS산전','H02K 7/116',2021,'인버터 구동 서보모터','FIG.2 블록도'),
            ('JP2022-089012 A','야스카와전기','B25J 9/00',2022,'직교 로봇 이송 시스템','FIG.1 정면도'),
            ('KR10-2023-0023456','현대로보틱스','B25J 17/02',2023,'다관절 로봇 손목 관절','FIG.3 상세도'),
            ('US11,349,218 B2','한화시스템','H01Q 1/12',2022,'위성 안테나 전개 메커니즘','FIG.1 전개도'),
            ('KR10-2021-0067890','두산공작기계','B23Q 3/157',2021,'CNC 자동교환장치','FIG.2 단면도'),
            ('KR10-2021-0190567','현대로템','A61H 1/02',2021,'외골격 보행 보조 구동부','FIG.2 정면도'),
            ('US10,906,124 B2','포스코','B23K 20/12',2021,'마찰교반 용접 공구','FIG.1 측면도'),
            ('KR10-2021-0112678','포항공대기술지주','G01N 15/14',2021,'단일세포 분석 플로우셀','FIG.2 단면도'),
            ('KR10-2020-0245678','비올㈜','A61B 17/32',2020,'지방흡입 캐뉼라 구조','FIG.1 상세도'),
        ]),
        ('전자·회로', [
            ('KR10-2021-0034521','삼성전자㈜','H02M 7/48',2021,'고효율 인버터 회로','FIG.1 회로도'),
            ('KR10-2022-0056789','LG전자㈜','H03K 17/687',2022,'H-브릿지 MOSFET 드라이버','FIG.2 회로도'),
            ('US11,031,951 B2','SK하이닉스','H03M 1/12',2021,'고분해능 ADC 샘플링','FIG.3 블록도'),
            ('KR10-2020-0123456','현대일렉트릭','H02M 3/155',2020,'PWM 전력 제어 모듈','FIG.1 블록도'),
            ('KR10-2023-0034567','삼성전기','H01G 4/30',2023,'적층 세라믹 커패시터','FIG.2 단면도'),
            ('EP3,852,197 A1','삼성전자㈜','H01Q 21/06',2021,'5G 밀리미터파 안테나 어레이','FIG.4 평면도'),
            ('KR10-2021-0089012','LG이노텍','H03F 3/193',2021,'고주파 RF 저잡음 증폭기','FIG.1 회로도'),
            ('US10,979,055 B2','삼성전자㈜','H03L 7/089',2021,'PLL 위상 고정 루프','FIG.3 블록도'),
            ('KR10-2022-0112345','삼성SDI','H02J 7/00',2022,'이차전지 BMS 보호 회로','FIG.2 회로도'),
            ('KR10-2021-0145678','LG전자㈜','H02J 50/10',2021,'무선충전 송수신 코일','FIG.1 평면도'),
            ('EP3,799,298 A1','현대일렉트릭','H03K 17/06',2021,'SiC MOSFET 게이트 드라이버','FIG.3 회로도'),
            ('KR10-2020-0067890','LS Electric','H03H 7/01',2020,'EMI 방사 저감 필터','FIG.2 회로도'),
            ('KR10-2023-0045678','LEM코리아','G01R 19/00',2023,'전류 센서 홀 소자 모듈','FIG.1 단면도'),
            ('US11,190,145 B2','네이버클라우드','G06F 1/02',2021,'FPGA 기반 디지털 제어기','FIG.4 블록도'),
            ('KR10-2021-0078901','LS Electric','H01F 27/28',2021,'토로이달 변압기 권선','FIG.1 단면도'),
            ('KR10-2022-0023456','LG디스플레이','H10K 59/122',2022,'OLED 구동 회로','FIG.2 회로도'),
            ('KR10-2021-0167890','SK하이닉스','H01L 23/36',2021,'반도체 패키지 열관리','FIG.5 단면도'),
            ('EP3,923,388 A1','한화시스템','G01S 7/03',2021,'레이더 송수신 모듈','FIG.1 블록도'),
            ('KR10-2023-0078012','삼성전자㈜','H02J 7/02',2023,'USB-C PD 충전 제어기','FIG.3 회로도'),
            ('KR10-2022-0034012','LG디스플레이','G06F 3/041',2022,'플렉서블 OLED 터치 패널','FIG.2 단면도'),
            ('KR10-2021-0056234','삼성전기','G01L 9/00',2021,'MEMS 압력 센서','FIG.1 단면도'),
            ('US11,228,470 B2','삼성전자㈜','H04L 25/02',2022,'고속 직렬 인터페이스 PHY','FIG.4 블록도'),
            ('KR10-2020-0089123','LG에너지솔루션','H01M 10/04',2020,'리튬이온 셀 레이아웃','FIG.2 평면도'),
            ('EP3,871,239 A1','한화파워반도체','H01L 29/778',2021,'갈륨나이트라이드 전력 소자','FIG.3 단면도'),
            ('KR10-2022-0089234','LG유플러스','H04B 10/40',2022,'광섬유 통신 트랜시버','FIG.1 블록도'),
            ('KR10-2021-0034890','삼성전자㈜','H04N 25/77',2021,'CMOS 이미지 센서 픽셀','FIG.2 단면도'),
            ('JP2022-134521 A','TDK코리아','H02M 3/28',2022,'고속 스위칭 전원 컨버터','FIG.1 회로도'),
            ('KR10-2020-0145012','한전KDN','G01R 22/06',2020,'스마트 미터 통신 모듈','FIG.3 블록도'),
            ('KR10-2023-0101234','LG이노텍','G01S 17/04',2023,'적외선 근접 센서 회로','FIG.1 회로도'),
            ('EP3,929,031 B1','삼성전자㈜','H02J 50/80',2022,'무선 전력 수신 정류기','FIG.2 블록도'),
            ('KR10-2021-0112890','LS Electric','G01R 1/20',2021,'고정밀 전류 분배기','FIG.4 회로도'),
            ('KR10-2022-0067012','리노공업','G01R 1/04',2022,'반도체 테스트 소켓','FIG.1 단면도'),
            ('KR10-2021-0178901','삼성전자㈜','G06V 40/13',2021,'초음파 지문 인식 센서','FIG.3 단면도'),
            ('KR10-2020-0056789','한화솔루션','G05F 1/67',2020,'태양전지 MPPT 제어기','FIG.2 블록도'),
            ('JP2021-089012 A','소니코리아','G10K 11/178',2021,'능동형 소음 제거 회로','FIG.1 블록도'),
            ('KR10-2023-0123456','삼성디스플레이','G09G 3/3258',2023,'마이크로LED 구동 드라이버','FIG.4 회로도'),
            ('KR10-2022-0178012','한전KDN','G01R 21/06',2022,'3상 전력계량 IC 설계','FIG.2 블록도'),
            ('KR10-2021-0234567','SK텔레콤','H04L 9/08',2021,'양자 암호 키분배 회로','FIG.1 블록도'),
            ('KR10-2020-0167890','LG이노텍','G01C 17/00',2020,'지자기 센서 3축 보정','FIG.3 블록도'),
            ('EP3,840,175 A1','삼성전자㈜','G05F 1/46',2021,'통합 전력 관리 칩','FIG.5 블록도'),
            ('KR10-2022-0089456','KAIST기술지주','H02J 50/20',2022,'RF 에너지 하베스팅','FIG.2 회로도'),
            ('KR10-2023-0045012','LG이노텍','H10N 10/13',2023,'열전 발전 모듈','FIG.3 단면도'),
            ('US11,380,993 B2','삼성전자㈜','H01Q 3/26',2022,'나노 안테나 위상 배열','FIG.2 평면도'),
            ('KR10-2020-0234567','LS Electric','H02K 3/30',2020,'모터 권선 절연 구조','FIG.1 단면도'),
            ('KR10-2022-0145678','SK하이닉스','H03M 1/06',2022,'고속 A/D 변환 파이프라인','FIG.4 블록도'),
            ('KR10-2021-0190123','현대일렉트릭','B60L 53/66',2021,'EV 충전 인프라 컨트롤러','FIG.2 블록도'),
            ('KR10-2023-0067123','LG이노텍','G01P 15/125',2023,'가속도 센서 온도 보상','FIG.3 블록도'),
            ('KR10-2020-0189234','하이디스','G06F 3/044',2020,'정전용량 터치 컨트롤러','FIG.2 블록도'),
            ('KR10-2021-0201456','현대자동차㈜','H01M 8/10',2021,'연료전지 스택 MEA','FIG.1 단면도'),
            ('KR10-2022-0156789','에티컨코리아','A61B 17/32',2022,'초음파 수술 나이프','FIG.4 단면도'),
        ]),
        ('소프트웨어', [
            ('KR10-2023-0056789','PYPI Inc.','G06N 3/08',2023,'특허 AI 멀티에이전트 파이프라인','FIG.1 흐름도'),
            ('KR10-2022-0134012','네이버㈜','G06F 9/50',2022,'분산 마이크로서비스 아키텍처','FIG.2 블록도'),
            ('KR10-2023-0023456','카카오㈜','G06F 11/36',2023,'AI 기반 코드 리뷰 시스템','FIG.3 흐름도'),
            ('US11,372,879 B2','쿠팡㈜','G06F 16/903',2022,'실시간 데이터 스트리밍','FIG.1 블록도'),
            ('KR10-2023-0089012','네이버클라우드','G06N 20/00',2023,'LLM 프롬프트 최적화','FIG.2 흐름도'),
            ('KR10-2022-0067890','카카오㈜','G06Q 30/06',2022,'그래프 기반 추천 엔진','FIG.4 블록도'),
            ('KR10-2021-0145012','삼성전자㈜','G06N 3/063',2021,'엣지 AI 추론 가속기','FIG.1 블록도'),
            ('KR10-2022-0189012','SK텔레콤','H04L 9/32',2022,'블록체인 합의 프로토콜','FIG.3 흐름도'),
            ('KR10-2023-0101234','네이버㈜','G06F 16/51',2023,'멀티모달 검색 인덱싱','FIG.2 블록도'),
            ('KR10-2021-0234567','KT㈜','G06F 11/07',2021,'실시간 이상 감지 시스템','FIG.1 흐름도'),
            ('EP3,933,620 A1','삼성전자㈜','G06N 20/20',2021,'연합학습 프라이버시 보호','FIG.4 블록도'),
            ('KR10-2022-0045678','네이버㈜','G06F 16/901',2022,'지식 그래프 구축 파이프라인','FIG.2 흐름도'),
            ('KR10-2023-0034890','카카오㈜','G06F 8/65',2023,'자동화 CI/CD 파이프라인','FIG.1 블록도'),
            ('KR10-2021-0078012','네이버클라우드','G06F 9/455',2021,'컨테이너 오케스트레이션','FIG.3 블록도'),
            ('US11,263,023 B2','쿠팡㈜','G06F 9/54',2022,'서버리스 이벤트 처리','FIG.2 흐름도'),
            ('KR10-2022-0112345','토스페이먼츠','G06F 21/62',2022,'멀티테넌트 SaaS 격리','FIG.4 블록도'),
            ('KR10-2023-0145678','카카오㈜','G06F 16/332',2023,'RAG 기반 질의응답 시스템','FIG.1 흐름도'),
            ('KR10-2022-0178012','네이버㈜','G06F 16/2452',2022,'자연어 SQL 변환 엔진','FIG.3 블록도'),
            ('KR10-2023-0012890','LG AI연구원','G06N 3/08',2023,'GPT 파인튜닝 워크플로우','FIG.2 흐름도'),
            ('KR10-2021-0167890','SK텔레콤','G06N 5/04',2021,'시계열 예측 앙상블 모델','FIG.1 블록도'),
            ('KR10-2022-0056012','네이버클라우드','G06F 12/084',2022,'분산 캐시 일관성 프로토콜','FIG.4 흐름도'),
            ('KR10-2021-0090123','KT㈜','H04L 67/1001',2021,'적응형 부하 분산 알고리즘','FIG.2 블록도'),
            ('KR10-2023-0023678','삼성전자㈜','G06N 3/0475',2023,'온디바이스 AI 모델 압축','FIG.1 흐름도'),
            ('KR10-2022-0134890','KAIST기술지주','G06F 12/14',2022,'커널 메모리 보호 구조','FIG.3 블록도'),
            ('KR10-2021-0145890','LG전자㈜','H04N 19/12',2021,'무손실 영상 압축 코덱','FIG.2 흐름도'),
            ('KR10-2022-0089123','토스㈜','G06F 16/23',2022,'분산 트랜잭션 2PC 프로토콜','FIG.1 블록도'),
            ('US11,315,239 B2','삼성전자㈜','G06F 12/0837',2022,'GPU 메모리 계층 최적화','FIG.4 블록도'),
            ('KR10-2021-0201234','SK텔레콤','G06Q 20/38',2021,'스마트 계약 검증 엔진','FIG.2 흐름도'),
            ('KR10-2022-0023012','카카오모빌리티','G01C 21/26',2022,'위치 기반 서비스 엔진','FIG.3 블록도'),
            ('KR10-2023-0056012','네이버㈜','G10L 21/013',2023,'실시간 음성 변환 엔진','FIG.1 흐름도'),
            ('KR10-2022-0167890','SK인포섹','H04L 9/40',2022,'제로 트러스트 인증 플로우','FIG.2 블록도'),
            ('KR10-2023-0078901','카카오㈜','G06F 8/33',2023,'AI 코드 자동완성 모델','FIG.4 흐름도'),
            ('KR10-2022-0045012','네이버㈜','G06T 15/00',2022,'메타버스 렌더링 파이프라인','FIG.1 블록도'),
            ('KR10-2021-0123456','LG AI연구원','G06N 20/20',2021,'AutoML 하이퍼파라미터 탐색','FIG.3 흐름도'),
            ('KR10-2023-0034012','네이버클라우드','G06Q 10/06',2023,'멀티클라우드 비용 최적화','FIG.2 블록도'),
            ('KR10-2022-0201234','카카오㈜','G06N 3/08',2022,'딥러닝 모델 서빙 시스템','FIG.1 흐름도'),
            ('KR10-2021-0089234','삼성리서치','G06N 3/045',2021,'그래프 신경망 추론 가속','FIG.4 블록도'),
            ('KR10-2022-0112678','KAIST기술지주','H04L 9/00',2022,'동형암호 연산 프레임워크','FIG.2 흐름도'),
            ('KR10-2023-0089456','PYPI Inc.','G06N 5/00',2023,'다중 에이전트 협업 프로토콜','FIG.1 블록도'),
            ('KR10-2021-0167012','쿠팡㈜','G06Q 30/0241',2021,'실시간 개인화 추천 시스템','FIG.3 흐름도'),
            ('KR10-2022-0145012','네이버㈜','G06F 16/21',2022,'스트리밍 ETL 처리 엔진','FIG.2 블록도'),
            ('KR10-2023-0023012','현대자동차㈜','G05D 1/02',2023,'자율주행 인지 파이프라인','FIG.1 흐름도'),
            ('KR10-2021-0201890','KT클라우드','G06F 11/20',2021,'클라우드 스토리지 복제','FIG.4 블록도'),
            ('KR10-2022-0234567','네이버㈜','G06N 3/044',2022,'Transformer 어텐션 최적화','FIG.2 블록도'),
            ('KR10-2023-0101890','삼성전자㈜','G06F 21/16',2023,'차분 프라이버시 메커니즘','FIG.3 흐름도'),
            ('KR10-2022-0056456','네이버㈜','G06F 16/2453',2022,'병렬 쿼리 실행 최적화기','FIG.1 블록도'),
            ('KR10-2021-0234890','토스㈜','G06F 16/27',2021,'이벤트 소싱 아키텍처','FIG.2 흐름도'),
            ('KR10-2023-0112012','안랩㈜','H04L 9/40',2023,'사이버 위협 탐지 AI','FIG.1 블록도'),
            ('KR10-2022-0078901','카카오㈜','G06V 20/40',2022,'실시간 영상 인식 엔진','FIG.4 흐름도'),
            ('KR10-2021-0112890','네이버클라우드','H04L 67/1036',2021,'서비스 메시 트래픽 제어','FIG.3 블록도'),
        ]),
        ('바이오·의료', [
            ('KR10-2021-0056789','셀트리온','C12Q 1/68',2021,'체외 DNA 시퀀싱 장치','FIG.1 단면도'),
            ('KR10-2022-0089012','삼성전자㈜','A61B 5/1455',2022,'비침습 혈당 측정 센서','FIG.2 블록도'),
            ('KR10-2021-0112345','올림푸스코리아','A61B 1/00',2021,'내시경 캡슐 구동 장치','FIG.1 단면도'),
            ('KR10-2020-0134567','오스템임플란트','A61F 2/38',2020,'무릎 인공관절 슬라이딩면','FIG.3 상세도'),
            ('EP3,804,627 A1','메드트로닉코리아','A61M 25/06',2021,'혈관 스텐트 전개 카테터','FIG.2 단면도'),
            ('KR10-2023-0034567','타이레바이오','A61M 37/00',2023,'주사형 마이크로니들','FIG.1 단면도'),
            ('KR10-2022-0045678','지멘스헬시니어스코리아','G01R 33/34',2022,'고해상도 MRI 코일 어레이','FIG.4 단면도'),
            ('US10,987,517 B2','보스턴사이언티픽코리아','A61N 1/362',2021,'이식형 심박조율기 회로','FIG.2 블록도'),
            ('KR10-2021-0178901','메드트로닉코리아','A61M 5/142',2021,'인슐린 자동 주입 펌프','FIG.1 단면도'),
            ('KR10-2022-0201234','큐렉소','A61B 34/30',2022,'수술 로봇 다관절 팔','FIG.3 정면도'),
            ('KR10-2023-0056012','KAIST기술지주','G01N 27/327',2023,'전기화학 바이오센서 칩','FIG.2 단면도'),
            ('KR10-2021-0090123','서울대기술지주','C12M 1/00',2021,'3D 오가노이드 배양 챔버','FIG.1 단면도'),
            ('EP3,865,211 A1','바이오니아','B01L 3/00',2021,'디지털 미세유체 플랫폼','FIG.4 평면도'),
            ('KR10-2022-0123456','씨젠㈜','C12Q 1/68',2022,'PCR 진단 키트 카트리지','FIG.2 단면도'),
            ('KR10-2020-0167890','오스템임플란트','A61B 17/70',2020,'척추 고정 나사 계류 구조','FIG.3 상세도'),
            ('KR10-2021-0201234','한국메드텍','A61F 2/24',2021,'인공 심장 판막 봉합 링','FIG.1 단면도'),
            ('KR10-2022-0145678','지멘스헬시니어스코리아','A61B 5/055',2022,'뇌 자기공명 헬멧 코일','FIG.2 단면도'),
            ('KR10-2023-0078901','뉴로핏','A61N 1/04',2023,'경두개 전기자극 전극','FIG.4 상세도'),
            ('KR10-2021-0056234','칼자이스코리아','G02B 21/16',2021,'형광 현미경 광학 경로','FIG.1 단면도'),
            ('KR10-2022-0034012','차의과학대기술지주','C12N 5/00',2022,'줄기세포 분화 배양 모듈','FIG.3 단면도'),
            ('KR10-2021-0089456','셀트리온','B01D 15/36',2021,'단백질 크로마토그래피 컬럼','FIG.2 단면도'),
            ('KR10-2020-0189012','청주의료기','A61L 2/07',2020,'고압증기 멸균 챔버 구조','FIG.1 단면도'),
            ('KR10-2023-0112345','포항공대기술지주','B01D 61/00',2023,'엑소좀 분리 마이크로채널','FIG.4 단면도'),
            ('EP3,849,411 A1','필립스코리아','A61B 8/00',2021,'광음향 영상화 탐촉자','FIG.2 단면도'),
            ('KR10-2022-0078012','코렌텍','A61B 17/04',2022,'복강경 봉합 장치','FIG.1 정면도'),
            ('KR10-2021-0134567','바이오니아','G01N 33/543',2021,'면역분석 ELISA 플레이트','FIG.3 단면도'),
            ('KR10-2022-0056789','고려대의료원','A61M 1/36',2022,'체외막산소화 ECMO 회로','FIG.2 블록도'),
            ('KR10-2023-0023234','현대로템','A61H 3/00',2023,'착용형 재활 외골격 조인트','FIG.1 정면도'),
            ('KR10-2021-0145234','한미약품','A61K 9/51',2021,'나노입자 약물 캡슐화','FIG.4 단면도'),
            ('KR10-2020-0212345','오스템임플란트','A61C 8/00',2020,'치과 임플란트 나사산','FIG.2 상세도'),
            ('KR10-2022-0189234','JMS코리아','A61M 1/16',2022,'혈액 투석 막 모듈','FIG.3 단면도'),
            ('KR10-2023-0067890','클래시스','A61N 1/30',2023,'피부 이온토포레시스 패치','FIG.1 단면도'),
            ('KR10-2021-0234012','루트로닉','A61F 9/008',2021,'레이저 안과 치료 광학계','FIG.2 단면도'),
            ('KR10-2022-0101234','T&R바이오팹','B29C 64/00',2022,'바이오프린팅 압출 헤드','FIG.4 단면도'),
            ('KR10-2021-0023456','인바디㈜','A61B 5/022',2021,'연속 혈압 모니터 커프','FIG.1 단면도'),
            ('KR10-2023-0145012','뉴로핏','A61N 1/05',2023,'경막외 전기자극 리드','FIG.3 상세도'),
            ('EP3,913,375 A1','진캐스트코리아','G01N 27/447',2021,'단분자 시퀀싱 나노포어','FIG.2 단면도'),
            ('KR10-2022-0034456','LG이노텍','G06V 40/14',2022,'생체인식 정맥 스캐너','FIG.1 블록도'),
            ('KR10-2021-0078456','코클리어코리아','A61N 1/36',2021,'인공와우 전극 어레이','FIG.4 단면도'),
            ('KR10-2023-0089678','클래시스','A61N 5/02',2023,'고주파 피부 리프팅 팁','FIG.2 단면도'),
            ('KR10-2022-0223456','한미약품','A61M 5/20',2022,'스마트 인슐린 패치','FIG.3 단면도'),
            ('KR10-2023-0034678','KAIST기술지주','B01L 3/00',2023,'마이크로유체 세포 분류기','FIG.1 단면도'),
            ('KR10-2021-0056890','바리안코리아','A61N 5/10',2021,'방사선 치료 콜리메이터','FIG.1 정면도'),
            ('KR10-2023-0178901','셀트리온','C12M 1/04',2023,'바이오리액터 DO 제어','FIG.4 블록도'),
            ('KR10-2022-0089890','삼성전자㈜','A61B 5/01',2022,'체온 이식 센서 패키지','FIG.2 단면도'),
            ('KR10-2021-0112678','포항공대기술지주','G01N 15/14',2021,'단일세포 분석 플로우셀','FIG.2 단면도'),
            ('KR10-2022-0267890','큐렉소','A61B 34/20',2022,'수술용 3D 내비게이션','FIG.3 블록도'),
            ('KR10-2021-0079234','포스코건설','E01D 19/12',2021,'폴리머 복합재 교량 바닥판','FIG.1 단면도'),
            ('KR10-2022-0101456','롯데건설㈜','E04G 23/02',2022,'탄소섬유 보강 기둥','FIG.4 단면도'),
            ('KR10-2021-0123678','한화솔루션','E04D 13/18',2021,'건물 일체형 태양광 지붕','FIG.2 단면도'),
        ]),
        ('화학·공정', [
            ('KR10-2021-0034012','롯데케미칼','B01D 3/14',2021,'진공 증류 분리 컬럼','FIG.1 단면도'),
            ('KR10-2022-0056234','LG화학','F28D 9/00',2022,'판형 열교환기 구조','FIG.2 단면도'),
            ('KR10-2021-0078901','한화솔루션','B01J 19/18',2021,'연속 교반 반응기','FIG.3 단면도'),
            ('KR10-2022-0101234','코오롱인더스트리','B01D 65/00',2022,'역삼투 분리막 모듈','FIG.1 단면도'),
            ('KR10-2020-0123456','효성티앤씨','B01J 3/04',2020,'고압 반응 용기 안전 밸브','FIG.4 단면도'),
            ('KR10-2023-0045678','롯데케미칼','B01F 27/112',2023,'터빈 임펠러 믹서','FIG.2 단면도'),
            ('EP3,811,409 A1','LG화학','B05B 7/04',2021,'이류체 분무 노즐 구조','FIG.1 단면도'),
            ('KR10-2021-0156789','SK이노베이션','B01D 25/12',2021,'수평 필터 프레스','FIG.3 단면도'),
            ('KR10-2022-0178012','GS칼텍스','B04B 1/04',2022,'원심 분리기 로터 구조','FIG.2 단면도'),
            ('KR10-2021-0200345','OCI㈜','B01D 9/00',2021,'결정화 냉각 탱크','FIG.1 단면도'),
            ('KR10-2020-0212567','한화솔루션','B01J 8/18',2020,'유동층 반응기 배플','FIG.4 단면도'),
            ('KR10-2023-0067890','SK이노베이션','B01J 23/40',2023,'고활성 촉매 펠렛 구조','FIG.2 단면도'),
            ('KR10-2022-0089234','에어리퀴드코리아','B01D 53/047',2022,'PSA 가스 흡착탑','FIG.3 블록도'),
            ('KR10-2021-0112456','코오롱인더스트리','B01D 53/22',2021,'폴리머 분리막 가스 모듈','FIG.1 단면도'),
            ('KR10-2022-0134678','LG생활건강','B01F 23/41',2022,'연속 유화 반응기','FIG.2 단면도'),
            ('KR10-2021-0156901','롯데케미칼','G05D 21/02',2021,'pH 자동 제어 시스템','FIG.4 블록도'),
            ('KR10-2020-0178123','KSB코리아','F04D 29/18',2020,'고효율 원심 펌프 임펠러','FIG.1 단면도'),
            ('KR10-2023-0089456','GS칼텍스','F28B 1/02',2023,'쉘앤튜브 응축기 설계','FIG.3 단면도'),
            ('EP3,857,220 A1','한화솔루션','B01D 1/22',2021,'낙하막 증발기 구조','FIG.2 단면도'),
            ('KR10-2022-0201567','한화파워시스템','F04D 17/12',2022,'6단 원심 압축기','FIG.1 단면도'),
            ('KR10-2021-0223789','롯데케미칼','B01J 47/00',2021,'이온교환 수지 충전탑','FIG.4 단면도'),
            ('KR10-2022-0245901','SK이노베이션','B01D 11/02',2022,'초임계 CO₂ 추출 챔버','FIG.2 단면도'),
            ('KR10-2021-0012123','코오롱인더스트리','B01D 61/42',2021,'전기투석 스택 구조','FIG.1 단면도'),
            ('KR10-2023-0034234','LG화학','B01J 19/00',2023,'마이크로 반응기 채널','FIG.3 단면도'),
            ('EP3,889,134 A1','한화솔루션','B01J 19/12',2021,'연속흐름 포토화학 반응기','FIG.2 단면도'),
            ('KR10-2022-0056456','롯데케미칼','B01D 1/18',2022,'스프레이 건조기 챔버','FIG.1 단면도'),
            ('KR10-2021-0078678','SK에코플랜트','C10B 53/00',2021,'고온 열분해 반응로','FIG.4 단면도'),
            ('KR10-2020-0100890','한화솔루션','B01J 19/00',2020,'기포탑 반응기 설계','FIG.2 단면도'),
            ('KR10-2023-0112567','SK이노베이션','C02F 1/46',2023,'전기화학 산화 셀 스택','FIG.3 블록도'),
            ('KR10-2022-0134789','GS칼텍스','B01J 38/02',2022,'촉매 재생 소성로','FIG.1 단면도'),
            ('KR10-2021-0157012','롯데케미칼','C10G 9/18',2021,'다관 열분해 튜브','FIG.4 단면도'),
            ('KR10-2022-0179234','코오롱인더스트리','C02F 3/12',2022,'폐수 막생물반응기','FIG.2 단면도'),
            ('KR10-2021-0201456','현대자동차㈜','H01M 8/10',2021,'연료전지 스택 MEA','FIG.1 단면도'),
            ('KR10-2023-0223678','한화에너지','C10J 3/00',2023,'바이오매스 가스화 로','FIG.3 단면도'),
            ('KR10-2022-0012345','포스코홀딩스','B01J 20/22',2022,'리튬 추출 흡착제 모듈','FIG.2 단면도'),
            ('KR10-2021-0034567','롯데케미칼','C01C 1/04',2021,'암모니아 합성 반응기','FIG.1 단면도'),
            ('KR10-2022-0056789','LG화학','B29C 48/30',2022,'고분자 필름 코팅 다이','FIG.4 단면도'),
            ('KR10-2020-0078901','한화솔루션','B01D 53/86',2020,'탈질 SCR 촉매 모듈','FIG.2 단면도'),
            ('KR10-2023-0101123','현대모비스','F17C 1/00',2023,'수소 저압 저장 탱크','FIG.1 단면도'),
            ('KR10-2022-0123345','한화에너지','F28D 20/00',2022,'고온 용융염 열저장','FIG.3 단면도'),
            ('KR10-2021-0145567','에어리퀴드코리아','F24F 3/14',2021,'회전형 흡착식 제습기','FIG.2 단면도'),
            ('KR10-2022-0167789','SK이노베이션','C12M 1/02',2022,'바이오에탄올 발효조','FIG.4 단면도'),
            ('KR10-2021-0190012','OCI㈜','C25B 9/19',2021,'멤브레인 전기분해 셀','FIG.1 단면도'),
            ('KR10-2023-0212234','롯데케미칼','B01J 3/00',2023,'수율 최적화 고압 반응기','FIG.3 단면도'),
            ('KR10-2022-0234456','한화솔루션','F26B 11/04',2022,'열풍 건조기 다단 트레이','FIG.2 단면도'),
            ('KR10-2021-0256678','OCI㈜','B01D 9/02',2021,'농축 증발 결정 시스템','FIG.1 블록도'),
            ('KR10-2020-0278890','두산에너빌리티','F28D 7/10',2020,'고온 가스 냉각 열교환기','FIG.4 단면도'),
            ('KR10-2023-0045890','OCI㈜','C30B 25/14',2023,'폴리실리콘 CVD 반응기','FIG.2 단면도'),
            ('KR10-2022-0067012','SK에코플랜트','B01D 53/18',2022,'고효율 스크러버 흡수탑','FIG.3 단면도'),
            ('KR10-2021-0089234','LG화학','B01D 9/02',2021,'연속 결정화 관형 반응기','FIG.1 단면도'),
        ]),
        ('구조·건축', [
            ('KR10-2021-0023456','현대건설㈜','E04C 3/08',2021,'하이브리드 철골 트러스','FIG.1 정면도'),
            ('KR10-2022-0045678','GS건설㈜','E01D 11/04',2022,'사장교 케이블 정착 구조','FIG.2 단면도'),
            ('KR10-2021-0067890','삼성물산㈜','E02D 5/22',2021,'PHC 말뚝 선단 확대부','FIG.3 상세도'),
            ('KR10-2022-0089012','한국유리공업','E04B 2/88',2022,'점착식 커튼월 패스너','FIG.1 단면도'),
            ('KR10-2021-0112234','대림건설㈜','E04H 9/02',2021,'점성 유체 댐퍼 장치','FIG.4 단면도'),
            ('KR10-2020-0134456','포스코건설','E04B 1/24',2020,'고력 볼트 마찰 접합부','FIG.2 상세도'),
            ('KR10-2023-0056678','현대건설㈜','E04C 3/20',2023,'프리스트레스트 슬래브보','FIG.1 단면도'),
            ('KR10-2022-0178901','삼성엔지니어링','F24F 11/00',2022,'이중 덕트 VAV 시스템','FIG.3 블록도'),
            ('KR10-2021-0201123','롯데건설㈜','E04B 1/76',2021,'통기층 외단열 복합패널','FIG.2 단면도'),
            ('KR10-2020-0223345','GS건설㈜','E02D 31/02',2020,'지하수 방수 이중 차단막','FIG.1 단면도'),
            ('KR10-2023-0045567','현대건설㈜','E04C 5/00',2023,'이방성 보강 슬래브 배근','FIG.4 단면도'),
            ('KR10-2022-0067789','포스코건설','B23K 9/173',2022,'플럭스 코어 용접 이음','FIG.2 상세도'),
            ('KR10-2021-0089901','대림건설㈜','F16B 31/00',2021,'고장력 앵커 볼트 조인트','FIG.3 단면도'),
            ('KR10-2022-0112023','삼성물산㈜','E04B 1/348',2022,'경량 모듈러 유닛 접합','FIG.1 정면도'),
            ('KR10-2021-0134245','한국유리공업','E06B 3/673',2021,'복층 유리 스페이서 구조','FIG.4 단면도'),
            ('KR10-2020-0156467','롯데건설㈜','E04B 1/94',2020,'내화 뿜칠 피복 시스템','FIG.2 단면도'),
            ('KR10-2023-0178689','현대건설㈜','E04C 3/04',2023,'X형 철골 좌굴 방지 보강재','FIG.1 단면도'),
            ('KR10-2022-0200901','GS건설㈜','E04F 17/00',2022,'공동주택 승강기 피트 방수','FIG.3 단면도'),
            ('KR10-2021-0223123','현대건설㈜','E01D 19/06',2021,'교량 신축이음 장치','FIG.2 단면도'),
            ('KR10-2022-0245345','삼성물산㈜','E04C 5/16',2022,'철근 커플러 기계식 이음','FIG.4 상세도'),
            ('KR10-2021-0012567','대림건설㈜','E02D 17/04',2021,'지하연속벽 H-파일 공법','FIG.1 단면도'),
            ('KR10-2023-0034789','현대엔지니어링','G05B 15/02',2023,'스마트 건물 에너지 관리','FIG.3 블록도'),
            ('KR10-2022-0057012','현대건설㈜','B28B 1/00',2022,'3D 프린팅 콘크리트 노즐','FIG.2 단면도'),
            ('KR10-2021-0046345','삼성물산㈜','B28C 5/42',2021,'콘크리트 믹서 트럭 드럼','FIG.1 단면도'),
            ('KR10-2022-0101456','롯데건설㈜','E04G 23/02',2022,'탄소섬유 보강 기둥','FIG.4 단면도'),
            ('KR10-2021-0123678','한화솔루션','E04D 13/18',2021,'건물 일체형 태양광 지붕','FIG.2 단면도'),
            ('KR10-2022-0145890','삼성물산㈜','E04B 1/24',2022,'초고층 아웃리거 구조','FIG.1 정면도'),
            ('KR10-2021-0168012','현대건설㈜','F24F 12/00',2021,'폐열 회수 환기 시스템','FIG.3 블록도'),
            ('KR10-2020-0190234','GS건설㈜','E04C 3/08',2020,'격자형 공간 트러스 지붕','FIG.4 단면도'),
            ('KR10-2023-0212456','현대건설㈜','E04H 9/02',2023,'탄성받침 면진 장치','FIG.2 단면도'),
            ('KR10-2022-0234678','대림건설㈜','F24F 11/77',2022,'지하 주차장 환기 제어','FIG.1 블록도'),
            ('KR10-2021-0257901','한국유리공업','E04B 2/96',2021,'건물 파사드 조인트 실링','FIG.3 상세도'),
            ('KR10-2022-0024123','삼성물산㈜','E04B 2/88',2022,'전면 유리 외장 지지 구조','FIG.2 단면도'),
            ('KR10-2022-0068567','현대건설㈜','E04G 21/12',2022,'철근망 자동 결속 장치','FIG.4 정면도'),
            ('KR10-2020-0090789','GS건설㈜','E02D 29/02',2020,'지오텍스타일 보강토 옹벽','FIG.2 단면도'),
            ('KR10-2023-0113012','롯데건설㈜','E04B 1/76',2023,'건물 외벽 진공 단열재','FIG.1 단면도'),
            ('KR10-2022-0135234','현대건설㈜','E04H 9/02',2022,'자기 유변 유체 댐퍼','FIG.3 단면도'),
            ('KR10-2021-0157456','삼성물산㈜','E04B 5/43',2021,'조립식 무량판 구조 시스템','FIG.2 정면도'),
            ('KR10-2022-0179678','대림건설㈜','E02D 27/12',2022,'마이크로파일 기초 접합','FIG.4 단면도'),
            ('KR10-2021-0201901','현대건설㈜','E04H 1/00',2021,'OSC 공장 제작 욕실 유닛','FIG.1 단면도'),
            ('KR10-2022-0224123','GS건설㈜','E21D 9/06',2022,'저심도 관통 쉴드 TBM','FIG.3 단면도'),
            ('KR10-2021-0246345','두산에너빌리티','E04H 12/08',2021,'풍력 타워 플랜지 볼트','FIG.2 상세도'),
            ('KR10-2023-0012567','현대건설㈜','G01M 5/00',2023,'스마트 콘크리트 균열 모니터','FIG.1 블록도'),
            ('KR10-2022-0034789','포스코건설','E04C 3/20',2022,'UHPC 초고강도 빔','FIG.4 단면도'),
            ('KR10-2021-0057012','GS건설㈜','E04B 1/66',2021,'반지하 공간 방수 디테일','FIG.2 단면도'),
            ('KR10-2022-0079234','현대엔지니어링','E01C 7/00',2022,'에너지 하베스팅 도로','FIG.1 단면도'),
            ('KR10-2021-0101456','현대건설㈜','G01M 5/00',2021,'스마트 교량 SHM 센서','FIG.3 블록도'),
            ('KR10-2023-0123678','대림건설㈜','E04C 2/12',2023,'CLT 구조 목재 패널','FIG.4 단면도'),
            ('KR10-2022-0145901','삼성물산㈜','E04B 1/24',2022,'주상복합 전이보 구조','FIG.1 단면도'),
            ('KR10-2022-0067890','현대건설㈜','E04H 9/02',2022,'세장비 제어 버티컬 트러스','FIG.2 정면도'),
        ]),
    ]
    # 도면 유형별 SVG 변형 목록 (카테고리 × 도면종류 조합으로 다양성 확보)
    CAT_SVGS = {
        '기계':     ['mech_a', 'mech_b', 'mech_c', 'block_a', 'block_b'],
        '전자·회로':['circuit_a', 'circuit_b', 'block_a', 'block_c', 'circuit_a'],
        '소프트웨어':['flow_a', 'flow_b', 'block_a', 'block_b', 'block_c'],
        '바이오·의료':['bio_a', 'bio_b', 'flow_a', 'block_a', 'bio_a'],
        '화학·공정':['chem_a', 'chem_b', 'block_b', 'flow_b', 'chem_a'],
        '구조·건축':['struct_a', 'struct_b', 'mech_a', 'block_a', 'struct_a'],
    }
    # 도면 종류 키워드로 SVG 오버라이드 (리스트로 로테이션)
    FIG_OVERRIDES = {
        '흐름도': ['flow_a', 'flow_b'],
        '순서도': ['flow_b', 'flow_a'],
        '플로우': ['flow_a', 'flow_b'],
        '블록도': ['block_a', 'block_b', 'block_c'],
        '구성도': ['block_b', 'block_a', 'block_c'],
        '시스템도': ['block_c', 'block_a', 'block_b'],
        '회로도': ['circuit_a', 'circuit_b'],
        '배선도': ['circuit_b', 'circuit_a'],
        '시퀀스': ['block_c', 'block_b'],
    }

    items = []
    num = 1
    for cat, rows in cats:
        variants = CAT_SVGS.get(cat, ['block_a', 'flow_a', 'circuit_a'])
        cat_count = 0
        for (pno, assignee, ipc, year, name, fig) in rows:
            # 도면 종류 키워드로 SVG 결정 (키워드 매칭 → 로테이션)
            svg_t = None
            for kw, svgs in FIG_OVERRIDES.items():
                if kw in fig:
                    svg_t = svgs[cat_count % len(svgs)]
                    break
            if svg_t is None:
                svg_t = variants[cat_count % len(variants)]
            items.append({
                'num': 'DWG-{:03d}'.format(num),
                'cat': cat,
                'svg_type': svg_t,
                'svg_url': f'/static/svgs/gallery/{svg_t}.svg',
                'name': name,
                'pno': pno,
                'assignee': assignee,
                'ipc': ipc,
                'year': year,
                'fig': fig,
                'seed': num,
            })
            num += 1
            cat_count += 1
    return items

_GALLERY_DATA = _build_gallery()

def agent_detail(request, slug):
    data = _AGENT_PAGES.get(slug)
    if not data:
        raise Http404
    ctx = {
        'agent': data,
        'agents_order': _PIPELINE_ORDER,
        'slug': slug,
    }
    return render(request, 'pages/agent_detail.html', ctx)


def drawing_gallery(request):
    cats = request.GET.get('cat', '전체')
    ctx = {
        'gallery_data': _GALLERY_DATA,
        'gallery_cats': ['전체', '기계', '전자·회로', '소프트웨어', '바이오·의료', '화학·공정', '구조·건축'],
        'active_cat': cats,
    }
    return render(request, 'pages/drawing_gallery.html', ctx)


@login_required(login_url='/accounts/signup/')
def pipeline(request):
    """Summary → Claim → Specification → Composer 순서로 에이전트를 순차 실행합니다."""
    result = None
    error = None
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'project_name':    request.POST.get('project_name', '').strip(),
            'problem_to_solve': request.POST.get('problem_to_solve', '').strip(),
            'prior_art_problem': request.POST.get('prior_art_problem', '').strip(),
            'core_technology': request.POST.get('core_technology', '').strip(),
            'expected_effect': request.POST.get('expected_effect', '').strip(),
        }
        missing = [k for k, v in form_data.items() if not v]
        if missing:
            error = '모든 항목을 입력해주세요.'
        else:
            try:
                result = _run_pipeline(form_data)
            except Exception as e:
                error = f'파이프라인 실행 오류: {e}'

    return render(request, 'accounts/pipeline.html', {
        'result': result,
        'error': error,
        'form_data': form_data,
    })


def _run_pipeline(form_data: dict) -> dict:
    from agents.schemas.summary import InventorInput
    from agents.summary.summary_agent import run_summary_agent
    from agents.claim.claim_agent import run_claim_agent
    from agents.specification.specification_agent import run_specification_agent
    from agents.composer.composer_agent import run_composer_agent

    steps = {}

    # ── Step 1: Summary ─────────────────────────────────
    inventor_input = InventorInput(**form_data)
    summary_out = run_summary_agent(inventor_input)
    steps['summary'] = summary_out.model_dump()

    # ── Step 2: Claim (현재 스켈레톤) ───────────────────
    state = {
        'user_input': form_data['core_technology'],
        'summary': steps['summary'],
        'prior_art': {},
        'drawings': {},
    }
    claim_out = run_claim_agent({'summary': steps['summary'], 'prior_art': {}})
    steps['claims'] = claim_out.model_dump()
    state['claims'] = steps['claims']

    # ── Step 3: Specification ───────────────────────────
    spec_out = run_specification_agent(state)
    steps['specification'] = spec_out if isinstance(spec_out, dict) else spec_out
    state['specification'] = steps['specification']

    # ── Step 4: Composer ────────────────────────────────
    composer_out = run_composer_agent(state)
    steps['composer'] = composer_out if isinstance(composer_out, dict) else composer_out

    return steps


def chat_view(request):
    from workspace.models import PatentProject
    projects = PatentProject.objects.filter(owner=request.user).order_by('-created_at') if request.user.is_authenticated else []
    return render(request, 'accounts/chat.html', {'projects': projects})


def chat_stream(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        body = json.loads(request.body)
        messages = body.get('messages', [])
        source = body.get('source', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(_REPO_ROOT, '.env'))
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    except Exception as e:
        return JsonResponse({'error': f'OpenAI 초기화 오류: {e}'}, status=500)

    _CHAT_SYSTEM = """당신은 PYPI의 특허 전문 AI 어시스턴트입니다.
역할: 특허 명세서 작성, 청구항 구성, 선행기술 분석에 관한 전문적 조언 제공.
소스 문서가 제공된 경우 해당 내용을 기반으로 구체적으로 답변하세요.
한국어로 답변 (사용자가 영어로 질문하면 영어로 답변)."""

    system_content = _CHAT_SYSTEM
    if source:
        system_content += f'\n\n[사용자 제공 소스 문서]\n{source[:4000]}'

    all_messages = [{'role': 'system', 'content': system_content}] + messages[-20:]

    def event_stream():
        try:
            stream = client.chat.completions.create(
                model=os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini'),
                messages=all_messages,
                stream=True,
                max_tokens=1500,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    data = json.dumps({'content': delta.content}, ensure_ascii=False)
                    yield f'data: {data}\n\n'
            yield 'data: [DONE]\n\n'
        except Exception as e:
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


def chat_upload(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'error': '파일이 없습니다'}, status=400)

    name = uploaded.name.lower()
    if uploaded.size > 200 * 1024 * 1024:
        return JsonResponse({'error': '200MB 이하 파일만 지원합니다.'}, status=400)

    try:
        if name.endswith('.pdf'):
            import fitz
            data = uploaded.read()
            doc = fitz.open(stream=data, filetype='pdf')
            pages = []
            for i, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    pages.append(f'[{i+1}페이지]\n{text.strip()}')
                if i >= 299:
                    pages.append('... (이후 페이지 생략)')
                    break
            page_count = len(doc)
            doc.close()
            extracted = '\n\n'.join(pages)
        elif name.endswith('.docx'):
            import docx as _docx, io
            doc = _docx.Document(io.BytesIO(uploaded.read()))
            extracted = '\n\n'.join(p.text for p in doc.paragraphs if p.text.strip())
            page_count = None
        elif name.endswith(('.txt', '.md', '.html', '.htm', '.csv')):
            extracted = uploaded.read().decode('utf-8', errors='replace')
            page_count = None
        else:
            return JsonResponse({'error': f'지원하지 않는 형식: {uploaded.name}'}, status=400)

        if not extracted.strip():
            return JsonResponse({'error': '텍스트를 추출할 수 없습니다.'}, status=400)

        return JsonResponse({
            'text': extracted,
            'filename': uploaded.name,
            'size': uploaded.size,
            'page_count': page_count,
            'char_count': len(extracted),
        })
    except Exception as e:
        return JsonResponse({'error': f'파일 처리 오류: {e}'}, status=500)


