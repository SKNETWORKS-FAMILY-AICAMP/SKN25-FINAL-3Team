from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from accounts.models import UserProfile
from django.contrib import messages

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        user_role = request.POST.get('role', 'inventor')

        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role=user_role)
            messages.success(request, '회원가입이 완료되었습니다!')

            return redirect('/accounts/login/')
        else:
            messages.error(request, '회원가입에 실패했습니다. 입력 내용을 확인해주세요.')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


def about(request):
    return render(request, 'pages/about.html')


def features(request):
    return render(request, 'pages/features.html')


def team(request):
    return render(request, 'pages/team.html')


def agents_overview(request):
    return render(request, 'pages/agents_overview.html')


AGENTS = {
    'consulting': {
        'num': 'I', 'name': '상담 에이전트', 'en': 'Consulting Agent',
        'desc': '발명자와 대화하며 특허에 필요한 4대 핵심 요소와 알고리즘 단계를 수집합니다.',
        'detail': (
            '2단계 슬롯 필링 방식으로 발명 정보를 수집합니다. '
            'Phase 1에서는 GPT-4o로 문제점·해결방법·차별성·기대효과 4개 필드의 충분성을 판정하고, '
            'GPT-4o-mini로 부족한 항목에 대한 자연스러운 후속 질문을 생성하여 모든 항목이 충족될 때까지 반복 대화합니다. '
            'PDF·DOCX·HWP 파일 업로드 시 Vision API(GPT-4o)로 도면을 분석합니다. '
            'Phase 2에서는 구현 수단·파라미터·핵심 로직·부가 기능·예외 처리 등 종속항용 심화 정보를 추출합니다. '
            '최종 저장 전 GPT-4o로 전문 용어를 정제(polish)하고, '
            '결과를 Consulting·AlgorithmStep·DetailElement DB 테이블에 저장합니다.'
        ),
        'inputs': ['발명 아이디어 자연어 입력', 'PDF·DOCX·HWP 파일 (선택)', '사용자 ID'],
        'outputs': [
            'Consulting DB: 문제점/해결방법/차별성/기대효과 요약',
            'AlgorithmStep DB: 단계별 알고리즘 시퀀스',
            'DetailElement DB: 심화 정보 5개 타입',
            'state["raw_log"]: 전체 대화 기록',
        ],
        'steps': [
            ('Phase 1 — 독립항 정보 수집',
             'GPT-4o가 문제점·해결방법·차별성·기대효과 4개 항목의 충분성(sufficient)을 판정합니다. '
             'GPT-4o-mini는 부족한 항목에 맞춰 자연스러운 후속 질문을 생성하고, '
             '모든 항목 sufficient=true + 알고리즘 3단계 이상이 될 때까지 대화를 반복합니다. '
             '토큰 절감을 위해 최근 6개 메시지만 컨텍스트 윈도우에 포함합니다.'),
            ('파일 분석 — Vision API (선택)',
             'PDF·DOCX·HWP 파일이 업로드되면 텍스트를 최대 4000자까지 추출합니다. '
             '도면 이미지가 포함된 경우 GPT-4o Vision API로 분석하여 '
             '500자 이내의 시각 분석 결과를 상담 컨텍스트에 추가합니다.'),
            ('Phase 2 — 종속항 심화 정보 수집',
             '독립항 정보 수집이 완료되면 종속항 작성을 위한 심화 정보를 추출합니다. '
             '구현 수단 / 핵심 파라미터 / 알고리즘 세부 로직 / 선택적 부가 기능 / 예외 처리 '
             '5개 타입별로 GPT-4o JSON 파싱으로 분류하여 수집합니다.'),
            ('용어 정제 (Polish)',
             '최종 저장 직전, GPT-4o(POLISH_MODEL)로 수집된 4개 요약 필드 전체를 '
             '특허 전문 용어로 정제합니다. 일상 표현이 특허 문체에 맞는 표현으로 변환됩니다.'),
            ('DB 저장',
             '정제된 데이터를 Consulting(4개 요약 필드)·AlgorithmStep(단계별 시퀀스)·'
             'DetailElement(심화 정보 5개 타입) 3개 테이블에 분리하여 저장합니다. '
             '동일 user_id·consultation_idx의 재실행 시 기존 데이터를 덮어씁니다.'),
        ],
        'active': True, 'action_url': 'dashboard', 'action_label': '대시보드로 이동',
    },
    'summary': {
        'num': 'II', 'name': '요약 에이전트', 'en': 'Summary Agent',
        'desc': '정규식 사전분석과 LLM을 결합하여 발명을 후속 에이전트가 처리할 수 있는 구조로 변환합니다.',
        'detail': (
            '두 단계로 발명 정보를 처리합니다. '
            '먼저 정규식 사전분석(regex_preanalyze)으로 핵심 기술 문장을 분해하여 '
            '구성요소·처리 단계·데이터·관계 후보를 추출하고 발명 그래프 시드와 route_hint를 생성합니다. '
            '이 사전분석 결과를 GPT-4o 프롬프트에 포함시켜 compact JSON(1800자 이내)을 생성합니다. '
            '출력에는 사람이 읽는 readable_summary(3~5문장)와 '
            '후속 에이전트용 structured_invention(구성요소 최대 6개·처리단계 최대 6개·차별점·기대효과 등)이 포함됩니다. '
            '입력에 없는 구체 수치나 구성은 생성하지 않는 generalization_policy를 엄격히 적용합니다.'
        ),
        'inputs': [
            'project_name, problem_to_solve, prior_art_problem, core_technology, expected_effect (5개 필드)',
            'feedback_history (이전 피드백 누적, 선택)',
        ],
        'outputs': [
            'readable_summary: 사람 대면용 한국어 요약 (3~5문장)',
            'structured_invention: 구성요소·처리단계·차별점·기대효과 구조화 데이터',
            'warnings: 불명확한 부분 목록',
            'details: 정규식 사전분석 결과 포함',
        ],
        'steps': [
            ('정규식 사전분석 (regex_preanalyze)',
             '입력된 core_technology 문장을 정규식으로 분해합니다. '
             '구성요소(명사구)·처리 단계(동사구)·데이터 흐름·관계 후보를 각각 추출하고, '
             'stores/controls/determines/selects_or_replaces 등 관계 엣지를 포함한 '
             'invention_graph 시드를 생성합니다.'),
            ('route_hint & claim_1 후보 분류',
             '정규식 분석 결과를 바탕으로 발명 유형을 '
             'method_like / system_like / storage_medium_related 중 하나로 판단합니다. '
             '청구항 1의 핵심 후보(claim_1_core_candidates)와 종속항 후보도 자동 분류합니다. '
             '이 힌트들은 LLM 프롬프트에 포함되어 hallucination을 줄이는 가이드로 작동합니다.'),
            ('GPT-4o 구조화 생성',
             '5개 입력 필드 + 정규식 사전분석 결과 + 청구항 rule 서브셋(토큰 절감용)을 '
             'GPT-4o에게 전달하여 compact JSON(1800자 이내)을 생성합니다. '
             '구성요소 최대 6개, 처리단계 최대 6개, 경고 최대 4개로 크기를 제한합니다.'),
            ('generalization_policy 적용',
             '입력 텍스트에 명시되지 않은 구체 수치·구성·효과는 절대 생성하지 않는 '
             'generalization_policy가 시스템 프롬프트에 강제됩니다. '
             '상위 포괄어(시스템/서버) 안의 내부 기능 단위만 별도 component로 분리합니다.'),
            ('피드백 반영',
             'feedback_history가 존재하면 이전 대화에서 사용자가 제공한 피드백을 '
             '프롬프트에 포함하여 반복 개선이 가능합니다. '
             '피드백 적용 여부는 feedback_applied 필드로 추적됩니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
    'prior-art': {
        'num': 'III', 'name': '선행기술조사 에이전트', 'en': 'Prior Art Agent',
        'desc': '청구항 1을 pgvector DB에서 임베딩 검색하고 LLM 병렬 분석으로 신규성·진보성 리스크를 판정합니다.',
        'detail': (
            '3단계로 선행기술을 조사합니다. '
            '먼저 독립항(청구항 1)을 text-embedding-3-small 모델로 임베딩하여 '
            'PostgreSQL pgvector의 cosine_distance로 유사 특허 Top-5를 검색합니다. '
            'IPC 코드 필터링도 지원합니다. '
            '이후 ThreadPoolExecutor(max_workers=5)로 각 후보 특허를 GPT-4o로 병렬 분석하여 '
            '중복점·차별점·근거 문장·리스크 등급(high/medium/low)을 판정합니다. '
            '전체 리스크는 high 건수 2개 이상이면 high, 1개 또는 medium 2개 이상이면 medium으로 자동 집계합니다. '
            '분석 실패 시 fallback 처리로 파이프라인이 중단되지 않습니다.'
        ),
        'inputs': [
            'claims_data (ClaimResult): 독립항 포함 청구항 리스트',
            'top_n: 검색 후보 수 (기본값 5)',
            'ipc_prefix: 기술분야 필터 (선택)',
        ],
        'outputs': [
            'candidates: 유사 특허 목록 (유사도·중복점·차별점·근거·리스크)',
            'overall_risk: 전체 리스크 등급 및 요약 (high/medium/low)',
            'analysis_summary: 자연어 종합 요약',
        ],
        'steps': [
            ('청구항 1 추출',
             'claims_data에서 claim_no=1인 독립항의 content 텍스트를 추출합니다. '
             '독립항이 여러 개인 경우 첫 번째 독립항을 검색 쿼리로 사용합니다.'),
            ('임베딩 변환',
             'OpenAI text-embedding-3-small 모델로 청구항 1 텍스트를 벡터로 변환합니다. '
             '임베딩 처리 시간과 비용은 로깅으로 추적됩니다.'),
            ('pgvector 유사 특허 검색',
             'PostgreSQL에 저장된 특허 임베딩 DB에서 cosine_distance 기준으로 '
             '가장 유사한 특허 Top-N을 검색합니다. '
             'similarity_score = 1 - distance/2 공식으로 변환하여 반환합니다. '
             'ipc_prefix가 제공된 경우 해당 기술분야 특허만 필터링합니다.'),
            ('병렬 LLM 분석',
             'ThreadPoolExecutor(max_workers=5)로 후보 특허 5개를 GPT-4o로 동시 분석합니다. '
             '각 특허에 대해 [본원 청구항 1] vs [선행특허 청구항 1/요약]을 비교하여 '
             '중복점·차별점·한계점·근거 문장·리스크 등급(high/medium/low)을 추출합니다. '
             '분석 실패 시 모든 필드를 empty로 채운 fallback 객체로 대체됩니다.'),
            ('전체 리스크 집계',
             'high 등급 2건 이상 → 전체 리스크 high (청구항 범위 조정 필요). '
             'high 1건 또는 medium 2건 이상 → medium (차별점 강조 필요). '
             '그 외 → low (현재 방향 진행 가능). '
             '_merge_unique() 로직으로 여러 후보의 중복 분석 내용을 자동 제거합니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
    'claim': {
        'num': 'IV', 'name': '청구항 에이전트', 'en': 'Claim Agent',
        'desc': '상담 DB 데이터를 재구성하여 독립항과 종속항으로 구성된 특허 청구항을 GPT-4o로 생성합니다.',
        'detail': (
            '상담 에이전트가 저장한 DB 데이터를 기반으로 청구항을 생성합니다. '
            'Consulting·AlgorithmStep·DetailElement 테이블에서 데이터를 조회하여 '
            '【1부 독립항】(문제/해결/차별/효과 + 단계별 알고리즘)과 '
            '【2부 종속항】(구현 수단/데이터/핵심 로직/부가 기능/예외 처리) 구조의 프롬프트를 구성합니다. '
            'GPT-4o로 특허 변리사 역할의 청구항을 JSON 형식으로 생성하며, '
            '동일 사용자·상담의 중복 회차는 덮어쓰기 처리합니다. '
            'LangGraph 파이프라인에서 Examiner·Rewrite 에이전트와 연동하여 '
            '심사 통과 또는 최대 2회 재작성 루프를 수행합니다.'
        ),
        'inputs': [
            'user_id, consultation_idx (DB 조회 키)',
            'Consulting DB: 4개 요약 필드',
            'AlgorithmStep DB: 단계별 알고리즘',
            'DetailElement DB: 심화 정보 5개 타입',
        ],
        'outputs': [
            'claim_1: 독립항 전문',
            'dependent_claims: 종속항 전문',
            'GeneratedClaim DB 테이블 저장',
        ],
        'steps': [
            ('DB 데이터 조회',
             'user_id와 consultation_idx를 키로 Consulting·AlgorithmStep·DetailElement '
             '3개 테이블에서 상담 데이터를 조회합니다. '
             'fetch_consultation_from_db() 함수가 각 테이블의 데이터를 하나의 구조화된 텍스트로 재구성합니다.'),
            ('프롬프트 구성',
             '재구성된 데이터를 두 파트로 나눠 프롬프트에 배치합니다. '
             '【1부 독립항】에는 문제점·해결방법·차별성·기대효과 + 단계별 알고리즘을 포함하고, '
             '【2부 종속항】에는 구현 수단·파라미터·핵심 로직·부가 기능·예외 처리를 포함합니다.'),
            ('GPT-4o 청구항 생성',
             '특허 변리사 역할의 시스템 프롬프트와 재구성된 발명 데이터로 GPT-4o를 호출합니다. '
             'JSON 형식으로 독립항 1개(claim_1)와 종속항 세트(dependent_claims)를 생성합니다. '
             '동일 회차의 기존 데이터가 있으면 덮어씁니다.'),
            ('Examiner 심사',
             'LangGraph 파이프라인에서 ExaminerAgent가 생성된 청구항을 심사합니다. '
             '신규성·진보성·기재 요건 등을 평가하여 is_approved 값을 결정합니다. '
             'revision_count 카운터로 재작성 횟수를 추적합니다.'),
            ('조건부 재작성 루프',
             'should_continue() 라우터가 is_approved=True 또는 revision_count ≥ 2이면 파이프라인을 종료합니다. '
             '그 외에는 RewriteAgent가 Examiner의 피드백을 반영해 청구항을 수정하고 '
             'examiner_node로 재진입합니다. 최대 2회 재작성이 가능합니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
    'drawing': {
        'num': 'V', 'name': '도면 에이전트', 'en': 'Drawing Agent',
        'desc': '명세서 텍스트에서 도면 구성을 LLM으로 추출하고 특허청 스타일 SVG를 자동 생성·검증합니다.',
        'detail': (
            '6단계 파이프라인으로 특허 도면을 생성합니다. '
            '①정규식으로 명세서에서 도면 목록("도 N은...")과 참조부호("100: 부호명")를 추출합니다. '
            '②GPT-4o-mini로 발명 유형(hardware/software/method/system/hybrid)과 '
            '권장 도면 타입(flowchart/block_diagram/sequence/ui_screen 등)·구성요소·프로세스 흐름을 JSON으로 추출합니다. '
            '③도면 타입별로 elements/relations 구조의 fig_design JSON을 생성합니다. '
            '④SvgCanvas로 특허청 실무 스타일 SVG를 렌더링합니다(오각형 터미널, 마름모 분기, 점선 박스 등). '
            '⑤품질 점수(0~100점, 통과 기준 75점)를 산정하고, 미달 시 GPT-4o-mini로 자동 수정합니다. '
            '⑥선택적으로 GPT-4o Vision API로 최종 PNG를 검수합니다.'
        ),
        'inputs': [
            'invention_text: 특허 명세서 전문',
            'app_num: 출원번호',
            'option flags: export_svg, export_png, vision_review, auto_repair',
        ],
        'outputs': [
            'SVG 파일: 특허청 스타일 벡터 도면',
            'PNG 파일: 변환본 (선택)',
            'validation_json: 품질 점수 및 검증 결과 (A≥90/B≥75/C≥60/D<60)',
            'vision_json: Vision API 검수 결과 (선택)',
            'metadata_json: 배치 생성 결과 정리',
        ],
        'steps': [
            ('정규식 파싱',
             '명세서 텍스트에서 "도 N은 ..." 패턴으로 도면 목록을 추출합니다. '
             '"100: 부호명" 패턴으로 참조부호 사전을 구성합니다. '
             '도면 타입은 flowchart / block_diagram / sequence / ui_screen / circuit / stateDiagram 중 '
             '본문 키워드를 분석하여 자동 분류합니다.'),
            ('LLM 구성요소 추출',
             'GPT-4o-mini로 발명 유형(hardware/software/method/system/hybrid)과 '
             '권장 도면 목록(타입·제목·목적), 구성요소 목록(ID/이름/타입/관계), '
             '프로세스 흐름(단계 ID/타입/분기), 주요 행위자를 JSON으로 추출합니다. '
             '명세서 15000자 입력 제한으로 토큰 비용을 최적화합니다.'),
            ('fig_design JSON 생성',
             '도면 타입별로 elements/relations 구조의 설계 JSON을 생성합니다. '
             'flowchart: terminal(시작/종료)·process·decision(분기) 변환. '
             'block_diagram: 컨테이너 + 내부/외부 요소. '
             'sequence: actor 간 동기/비동기 메시지 흐름. '
             'API·네트워크·화면·센서 등 발명 특성에 따라 부족한 도면 타입을 자동 추가합니다.'),
            ('SVG 렌더링',
             'SvgCanvas로 특허청 실무 스타일 SVG를 렌더링합니다. '
             'NanumGothic/Noto Sans 폰트, 지정된 선 굵기, 마커 스타일을 고정 적용합니다. '
             '참조부호 leader line을 자동으로 배치하고, '
             '요소 우선순위(컨테이너/부/모듈/서버)에 따라 배치 순서를 결정합니다.'),
            ('품질 검증 및 자동 수정',
             'validate_fig()로 필수 필드·ID 중복·relation 노드 존재를 검사합니다. '
             'score_quality()로 요소 수(3개 이상), 참조부호 표시율, 도면 타입 유효성 등을 채점합니다(0~100점). '
             '75점 미달 시 GPT-4o-mini가 수정 제안을 생성하고 재렌더링합니다(최대 1회). '
             '최종 등급은 A(≥90)/B(≥75)/C(≥60)/D(<60)로 부여됩니다.'),
            ('Vision 검수 (선택)',
             'vision_review=True인 경우 cairosvg 또는 ImageMagick으로 PNG를 생성합니다. '
             'GPT-4o Vision API로 PNG 이미지를 분석하여 '
             '인식된 구성요소·연결선·도면 타입·참조부호 정확성과 시각적 품질 점수를 반환합니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
    'specification': {
        'num': 'VI', 'name': '명세서 에이전트', 'en': 'Specification Agent',
        'desc': '5개 에이전트 결과를 종합하여 특허 명세서 7개 섹션을 생성하고 절대 규칙으로 품질을 검증합니다.',
        'detail': (
            '요약·청구항·도면·선행기술 결과를 통합하여 특허 명세서 전체를 작성합니다. '
            'GPT-4o에게 5가지 절대 규칙(state 외 구성요소 신규 생성 금지, 허용되지 않은 참조부호/문헌번호 금지, '
            '근거 없는 정량 수치 금지, JSON 외 텍스트 금지)을 적용하여 '
            '기술분야·배경기술·해결과제·해결수단·효과·도면간단설명·상세설명 7개 섹션을 생성합니다. '
            '생성 후 절대 규칙 위반과 스타일 경고를 자동 검증하며, '
            '미통과 시 최대 3회까지 수정 프롬프트로 GPT-4o를 재호출합니다. '
            '최종적으로 동의어를 canonical_name으로 통일하고, '
            'MVP 정책에 따라 3회 후에도 미통과 시 경고와 함께 파이프라인을 계속 진행합니다.'
        ),
        'inputs': [
            'summary_data: 요약 에이전트 출력',
            'claims_data: 청구항 에이전트 출력',
            'prior_art_data: 선행기술조사 에이전트 출력',
            'drawings_data: 도면 에이전트 출력 (도면목록·참조부호)',
            'drafting_options: 작성 옵션 (방법항 단계 라벨 사용 여부 등)',
        ],
        'outputs': [
            '7개 섹션: 기술분야/배경기술/해결과제/해결수단/효과/도면간단설명/상세설명',
            'validation: 절대규칙 위반 여부 및 스타일 경고',
            'support_matrix: 청구항 요소별 명세서 지원 여부',
            'term_normalization: 용어 통일 기록',
        ],
        'steps': [
            ('자료 수집 및 화이트리스트 구성',
             'state에서 구성요소·처리단계·청구항·도면·참조부호·선행문헌 데이터를 추출합니다. '
             'allowed_terms(허용 용어 사전), allowed_ref_numerals(참조부호 화이트리스트), '
             'allowed_pub_numbers(선행문헌번호 화이트리스트)를 구성하여 '
             '이후 검증 단계의 기준으로 사용합니다.'),
            ('절대 규칙 프롬프트 구성',
             '5가지 절대 규칙을 시스템 프롬프트에 포함합니다: '
             '① state에 없는 구성요소 신규 생성 금지, '
             '② 허용 외 참조부호 사용 금지, '
             '③ 허용 외 선행문헌번호 사용 금지, '
             '④ 근거 없는 정량 수치(수치+단위 조합) 생성 금지, '
             '⑤ JSON 외 텍스트 출력 금지. '
             '섹션별 작성 원칙(배경기술 출처 표시, 해결수단 청구항 우선 근거 등)도 함께 제공합니다.'),
            ('GPT-4o 7개 섹션 일괄 생성',
             'response_format={"type": "json_object"}를 강제하여 GPT-4o로 7개 섹션을 한 번에 생성합니다. '
             '섹션별 세부 지침에 따라 technical_field(1~2문장), background_art(선행문헌 자연어 풀이), '
             'means_for_solving(청구항 독립항 우선 근거), detailed_description(도면 번호순 실시예)을 작성합니다.'),
            ('자동 검증',
             'validate_specification()이 절대 규칙 위반(hard_issues)과 스타일 경고(style_warnings)를 감지합니다. '
             '허용 외 참조부호·구성요소·문헌번호 포함 여부와 '
             '반복 명사구, 섹션별 과다 길이, 잘못된 내용 배치 등을 자동으로 검출합니다.'),
            ('최대 3회 자동 수정',
             '검증 미통과 시 이전 출력 + 실패 이유 + 수정 지시를 담은 프롬프트로 GPT-4o를 재호출합니다. '
             '최대 3회(max_repair_attempts=3) 반복하며, '
             '3회 후에도 미통과 시 warnings에 이슈를 기록하고 status="ok"로 파이프라인을 계속 진행합니다(MVP 정책).'),
            ('용어 정규화',
             'normalize_terms_across_outputs()로 명세서 전체의 동의어를 canonical_name으로 통일합니다. '
             '정규화 후 재검증을 수행하며, '
             '청구항 요소와 명세서 문단 간 지원 관계를 support_matrix에 기록합니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
    'composer': {
        'num': 'VII', 'name': '컴포저 에이전트', 'en': 'Composer Agent',
        'desc': 'LangGraph로 구성된 파이프라인의 오케스트레이터로, 에이전트 실행 순서와 품질 검토 루프를 관리합니다.',
        'detail': (
            'LangGraph StateGraph를 사용하여 전체 파이프라인을 조율합니다. '
            'summary_node → claim_node → examiner_node 순서로 실행하며, '
            'should_continue() 함수가 심사 결과(is_approved)와 재작성 횟수(revision_count)를 판단하여 '
            '승인 또는 최대 2회 재작성 시 END, 그 외에는 rewrite_node로 분기합니다. '
            '각 에이전트는 PatentAgentState를 공유하며 '
            'workflow·messages·summary·prior_art·claims·drawings·specification·'
            'document_links·invention_graph·drafting_options·composer·review·final_package '
            '등 13개 도메인 키로 구성된 상태를 통해 데이터를 전달합니다. '
            '최종 패키지에는 제목·초록·청구항·도면·명세서·선행기술보고서·검토보고서가 포함됩니다.'
        ),
        'inputs': [
            'PatentAgentState: 13개 도메인 키로 구성된 파이프라인 공유 상태',
            'InventorInput: project_name, problem_to_solve, prior_art_problem, core_technology, expected_effect',
        ],
        'outputs': [
            'final_package: 제목·초록·청구항·도면·명세서·선행기술보고서·검토보고서',
            'rendered_markdown / rendered_html_path / rendered_docx_path: 최종 출력 포맷',
            'review.consistency_score: 전체 일관성 점수',
        ],
        'steps': [
            ('LangGraph StateGraph 구성',
             'LangGraph의 StateGraph(PatentAgentState)로 파이프라인 그래프를 정의합니다. '
             'summary_node·claim_node·examiner_node·rewrite_node를 노드로 추가하고 '
             'START → summary_node → claim_node → examiner_node 순서로 엣지를 연결합니다.'),
            ('공유 상태(PatentAgentState) 관리',
             'TypedDict 기반의 PatentAgentState가 에이전트 간 데이터를 전달합니다. '
             'workflow(실행 상태)·messages·summary·prior_art·claims·drawings·specification·'
             'document_links·invention_graph·drafting_options·composer·review·final_package '
             '등 13개 도메인 키로 구성됩니다.'),
            ('summary_node 실행',
             'SummaryAgent.run()을 호출하여 발명 정보를 구조화합니다. '
             '결과는 state["summary"]에 readable_summary와 structured_invention으로 저장됩니다. '
             'structured_invention은 이후 모든 에이전트의 입력 기반이 됩니다.'),
            ('claim_node 실행',
             'ClaimAgent.run()을 호출하여 독립항·종속항 청구항을 생성합니다. '
             '결과는 state["claims"]에 저장되며, '
             'claim_dependency_graph와 independent/dependent_claim_numbers도 함께 기록됩니다.'),
            ('examiner_node → should_continue() 조건 분기',
             'ExaminerAgent.run()이 청구항을 심사하고 is_approved와 revision_count를 갱신합니다. '
             'should_continue()가 is_approved=True 또는 revision_count ≥ 2이면 END로 라우팅하고, '
             '그 외에는 rewrite_node로 분기하여 RewriteAgent가 청구항을 수정 후 '
             'examiner_node로 재진입합니다. 최대 2회 루프가 가능합니다.'),
            ('최종 패키지 조립 및 렌더링',
             '파이프라인 종료 후 각 에이전트 출력을 final_package에 통합합니다. '
             '제목·초록·청구항·도면·명세서·선행기술보고서·검토보고서가 하나의 패키지로 조립됩니다. '
             'rendered_markdown, rendered_html_path, rendered_docx_path 포맷으로 최종 출력됩니다.'),
        ],
        'active': False, 'action_url': None, 'action_label': '',
    },
}


def agent_detail(request, slug):
    agent = AGENTS.get(slug)
    if not agent:
        from django.http import Http404
        raise Http404
    return render(request, 'pages/agent_detail.html', {'agent': agent, 'slug': slug})


def drawing_gallery(request):
    return render(request, 'pages/drawing_gallery.html')


def insights(request):
    return render(request, 'pages/insights.html')


QNA_SECTIONS = [
    {
        'id': 'basics', 'section': '출원 기초', 'en': 'Filing Basics',
        'items': [
            ('특허 출원이란 무엇인가요?', '특허 출원은 발명자가 자신의 발명을 특허청에 등록하여 독점적 권리를 인정받는 절차입니다. 출원서, 명세서, 청구항, 도면 등의 서류를 특허청에 제출합니다.'),
            ('특허 출원 비용은 얼마인가요?', '특허 출원 비용은 출원료, 심사 청구료, 등록료 등으로 구성됩니다. 개인 발명자는 감면 혜택을 받을 수 있으며, 변리사 수임료가 별도로 발생합니다.'),
            ('특허 출원 후 얼마나 걸리나요?', '일반 심사는 출원 후 평균 14~18개월이 소요됩니다. 우선심사를 신청하면 2~3개월 내에 결과를 받을 수 있습니다.'),
            ('PCT 국제 출원이란 무엇인가요?', 'PCT(특허협력조약)를 통해 하나의 출원으로 다수 국가에 동시에 출원 효과를 가질 수 있습니다. 국제 출원일로부터 30개월 내에 각국 국내 단계에 진입해야 합니다.'),
        ]
    },
    {
        'id': 'claims', 'section': '청구항 작성', 'en': 'Claims Drafting',
        'items': [
            ('청구항이란 무엇인가요?', '청구항은 특허로 보호받고자 하는 발명의 범위를 구체적으로 기재한 항목입니다. 독립항과 종속항으로 구성되며, 법적 보호 범위를 결정합니다.'),
            ('독립항과 종속항의 차이는?', '독립항은 다른 청구항을 인용하지 않고 독립적으로 기재된 청구항입니다. 종속항은 독립항 또는 다른 종속항을 인용하여 추가 한정 사항을 기재합니다.'),
            ('청구항 작성 시 주의사항은?', '청구항은 명확하고 간결하게 작성해야 하며, 발명의 필수 구성요소만을 포함해야 합니다. 너무 좁게 작성하면 보호 범위가 줄고, 너무 넓게 작성하면 거절될 수 있습니다.'),
        ]
    },
    {
        'id': 'exam', 'section': '심사·등록', 'en': 'Examination',
        'items': [
            ('특허 거절 이유에는 어떤 것이 있나요?', '신규성 결여, 진보성 결여, 산업상 이용 가능성 부재, 기재 불비 등이 주요 거절 이유입니다. 거절이유통지를 받으면 의견서와 보정서를 제출하여 대응할 수 있습니다.'),
            ('의견서란 무엇인가요?', '심사관의 거절이유에 대응하여 출원인이 제출하는 서류입니다. 심사관의 판단에 동의하지 않는 이유를 논리적으로 설명하거나 보정서와 함께 제출합니다.'),
            ('특허 등록 후 권리 유지는?', '특허권은 등록일로부터 출원일 후 20년간 유지됩니다. 매년 특허 연차료를 납부해야 하며, 미납 시 권리가 소멸됩니다.'),
        ]
    },
    {
        'id': 'ai', 'section': 'AI 특허 Q&A', 'en': 'AI Patent Q&A',
        'items': [
            ('AI가 발명자가 될 수 있나요?', '현재 대부분의 국가에서 AI는 발명자로 인정되지 않습니다. 발명자는 자연인이어야 하며, AI를 도구로 사용한 인간이 발명자가 됩니다.'),
            ('AI 생성 발명의 특허성은?', 'AI가 생성한 발명도 신규성, 진보성 등 특허 요건을 충족하면 특허를 받을 수 있습니다. 단, AI를 활용한 인간의 창작 기여가 중요합니다.'),
            ('PYPI는 어떻게 특허 작성을 자동화하나요?', 'PYPI는 7개의 전문 AI 에이전트가 협력하는 파이프라인으로, 발명 아이디어 입력부터 완성 명세서 출력까지 전 과정을 자동화합니다. 각 에이전트는 LangGraph 기반으로 구성되어 있습니다.'),
            ('AI가 작성한 특허 명세서의 품질은?', 'PYPI는 특허청 제출 규격에 맞는 명세서를 생성합니다. 실제 등록 변리사의 자문을 바탕으로 설계된 프롬프트와 파이프라인을 사용하여 높은 품질의 명세서를 작성합니다.'),
        ]
    },
]


def qna(request):
    total_count = sum(len(s['items']) for s in QNA_SECTIONS)
    return render(request, 'pages/qna.html', {
        'qna_sections': QNA_SECTIONS,
        'total_count': total_count,
    })
