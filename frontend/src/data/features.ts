export interface FeatureStep {
  title: string
  detail: string
}

export interface FeatureSpec {
  label: string
  value: string
}

export interface FeatureDetail {
  slug: string
  name: string
  tagline: string
  description: string
  quote?: string
  steps: FeatureStep[]
  specs: FeatureSpec[]
  sourceFiles: string[]
}

export const FEATURES: FeatureDetail[] = [
  {
    slug: 'patent-search',
    name: '특허 검색',
    tagline: 'KIPRIS 특허 데이터베이스를 키워드로 즉시 검색합니다',
    description:
      '발명 키워드를 입력하면 KIPRIS(특허정보검색서비스) Open API의 getAdvancedSearch 엔드포인트를 직접 호출해, 실제 등록·공개 특허 데이터를 그 자리에서 조회합니다.',
    steps: [
      { title: '키워드 인코딩', detail: '입력한 검색어를 URL 인코딩하여 KIPRIS word 파라미터로 전달합니다.' },
      { title: 'KIPRIS Open API 호출', detail: 'GET patUtiModInfoSearchSevice/getAdvancedSearch 엔드포인트에 ServiceKey, numOfRows=10과 함께 요청합니다.' },
      { title: 'XML → JSON 변환', detail: 'xmltodict로 응답 XML을 파싱하고, 단일 결과/다중 결과를 모두 리스트로 정규화합니다.' },
      { title: '필드 매핑', detail: 'inventionTitle/applicationNumber/applicantName/applicationDate/astrtCont를 title/applicationNumber/applicant/date/abstract로 매핑해 반환합니다.' },
    ],
    specs: [
      { label: 'Endpoint', value: 'GET /patent-search' },
      { label: '외부 API', value: 'KIPRIS getAdvancedSearch' },
      { label: '결과 수', value: '고정 10건 (numOfRows=10)' },
      { label: '페이지네이션', value: '미지원' },
      { label: '캐싱', value: '없음 (매 요청마다 실시간 조회)' },
    ],
    sourceFiles: ['backend/fastapi/routers/patent_search.py'],
  },
  {
    slug: 'prior-art',
    name: 'AI 선행기술조사',
    tagline: 'AI가 기술분야를 판별해 최적의 검색 경로를 자동으로 선택합니다',
    description:
      '청구항 1항을 분석해 AI/SW 기술인지 비-AI(기계·화학·바이오 등) 기술인지를 LLM 라우터가 먼저 판별합니다. AI 기술이면 자체 pgvector DB에서, 비-AI 기술이면 KIPRIS 외부 API에서 유사 특허를 찾고, 각 후보를 LLM이 다시 한 건씩 정밀 분석해 위험도를 산출합니다.',
    quote: '"당신은 특허 검색 라우터 에이전트입니다. 입력된 청구항 내용을 분석하여, AI 기술이면 search_similar_patents를, 비-AI 기술이면 search_external_api 도구를 호출하세요."',
    steps: [
      { title: '라우팅 판단', detail: 'gpt-4o가 OpenAI function-calling으로 search_similar_patents / search_external_api 중 하나를 선택합니다.' },
      { title: 'AI 기술 → 로컬 DB 검색', detail: 'text-embedding-3-small로 임베딩 후, PostgreSQL pg_trgm 트라이그램으로 500건 사전 필터링 → pgvector IVFFlat 코사인 거리로 top-5 재정렬.' },
      { title: '비-AI 기술 → KIPRIS 검색', detail: 'gpt-4o-mini가 청구항을 (센서+감지기)*(무선+블루투스) 형태의 KIPRIS 쿼리로 변환, ThreadPoolExecutor로 각 특허의 청구항1·PDF를 병렬 조회.' },
      { title: '특허별 정밀 분석', detail: '변리사 역할의 gpt-4o가 본원 청구항과 선행특허를 1:1 비교해 overlap_points/difference_points/evidence_sentences/risk_level(JSON)을 산출, 최대 5건 병렬 처리.' },
      { title: '종합 위험도 산정', detail: 'high 2건 이상 → high, high 1건 또는 medium 2건 이상 → medium, 그 외 → low 로 규칙 기반 종합.' },
    ],
    specs: [
      { label: '라우팅 모델', value: 'gpt-4o (function calling)' },
      { label: '임베딩 모델', value: 'text-embedding-3-small (1536차원)' },
      { label: 'DB 인덱스', value: 'pgvector IVFFlat, cosine distance' },
      { label: '사전 필터', value: 'pg_trgm 트라이그램 500건 풀' },
      { label: '병렬 분석', value: 'ThreadPoolExecutor, 기본 max_workers=5' },
      { label: 'KIPRIS 타임아웃', value: '목록 10초 / 상세 5초' },
    ],
    sourceFiles: ['agents/prior_art_agent/prior_art_agent.py', 'agents/prior_art_agent/patent_db.py'],
  },
  {
    slug: 'claim-drafting',
    name: '청구항 작성',
    tagline: '발명 구성요소를 분석해 독립항·종속항을 자동으로 작성합니다',
    description:
      '구성요소(Components)·데이터 흐름(Data Flows)·처리 단계(Processing Steps)로 구조화된 발명 데이터를 바탕으로, 방법·시스템·CRM 3개 카테고리의 독립항과 그에 따른 종속항을 한 번의 LLM 호출로 생성합니다.',
    quote: '"청구항 내에서 구성요소나 데이터가 최초로 등장할 때는 상기를 붙이지 않습니다. 이미 등장한 구성요소를 다시 지칭할 때는 반드시 상기를 붙여야 합니다."',
    steps: [
      { title: '발명 데이터 주입', detail: '발명 명칭·해결 과제·구성요소 수·처리 단계 수·데이터 흐름 수를 프롬프트 변수로 채웁니다.' },
      { title: '독립항 3건 생성', detail: '방법/시스템/CRM 카테고리별로 독립항 1개씩, 메인 카테고리가 제1항이 됩니다.' },
      { title: '종속항 자동 분량 산정', detail: '권장 종속항 수 = max(구성요소 수, 처리 단계 수)를 프롬프트에 명시해 권리범위를 세분화합니다.' },
      { title: '선행기재 요건 적용', detail: '구성요소·데이터명이 처음 등장할 땐 "상기" 없이, 재등장할 땐 "상기"를 붙이도록 규칙화된 프롬프트로 강제합니다.' },
      { title: 'JSON 스키마 강제 출력', detail: 'claim_no/is_dependent/cited_claim_no/category/content 필드를 strict JSON Schema로 검증해 파싱합니다.' },
    ],
    specs: [
      { label: 'LLM', value: 'gpt-4o' },
      { label: 'Temperature', value: '0.3' },
      { label: 'Max tokens', value: '8192' },
      { label: '출력 형식', value: 'json_schema (strict=True)' },
      { label: '카테고리', value: '방법 · 시스템 · CRM' },
      { label: '재시도', value: '없음 (단일 호출, 실패 시 None 반환)' },
    ],
    sourceFiles: ['agents/claim_agent.py', 'backend/fastapi/routers/claims.py'],
  },
  {
    slug: 'examiner',
    name: '명확성 심사',
    tagline: '특허법 제42조 제4항 제2호 기준으로 청구항을 자동 심사·재작성합니다',
    description:
      '통상의 기술자 관점에서 청구항이 명확한지를 4가지 거절 기준(결합관계 부재·기능적 표현 한계·모호한 수치 표현·카테고리 불비)으로 심사합니다. 거절되면 ClaimRewriteAgent가 지적된 청구항만 최소 수정해 다시 제출하고, 최대 2회까지 이 루프를 반복합니다.',
    quote: '"청구항은 발명이 명확하고 간결하게 적혀 있어야 합니다 — 특허법 제42조 제4항 제2호"',
    steps: [
      { title: '1차 심사', detail: '커스텀 vLLM 모델(exaone-3.5-7.8B-custom)이 4가지 기준으로 청구항 전체를 검토, is_approved/rejections를 JSON으로 반환합니다.' },
      { title: '승인 또는 반려 분기', detail: 'is_approved가 true면 즉시 종료, false면 ClaimRewriteAgent로 보정 루프에 진입합니다.' },
      { title: '최소 침습 재작성', detail: '거절된 청구항만 수정하고 청구항 수·번호·카테고리·인용관계는 절대 변경하지 않도록 규칙화된 gpt-4o가 재작성합니다.' },
      { title: '재심사 및 종료 조건', detail: 'revision_count가 2에 도달하거나 승인되면 루프를 종료합니다 (최대 2회 보정).' },
    ],
    specs: [
      { label: '심사 모델', value: 'RunPod vLLM (exaone-3.5-7.8B-custom)' },
      { label: 'Temperature', value: '0.1' },
      { label: 'Max tokens', value: '4096' },
      { label: '재작성 모델', value: 'gpt-4o (temperature 0.1)' },
      { label: '최대 보정 횟수', value: '2회' },
      { label: '별도 모드', value: '/review-claims — 직접 입력한 청구항만 심사하는 BETA 플로우' },
    ],
    sourceFiles: ['agents/examiner.py', 'agents/claim_rewrite_agent.py', 'agents/core/graph.py'],
  },
  {
    slug: 'drawing',
    name: '도면 생성',
    tagline: '발명 구조를 시스템 블록도와 흐름도로 자동 시각화합니다',
    description:
      '구성요소·데이터 흐름·처리 단계를 Graphviz DOT 언어로 변환해 도1(시스템 구성도)과 도2(방법 흐름도) 2종의 도면을 자동 생성합니다. LLM 호출 없이 순수 템플릿 기반으로 동작해, 매번 동일한 입력에 대해 동일한 결과가 나옵니다.',
    steps: [
      { title: '도1 — 시스템 구성도', detail: '컴포넌트를 타입별(MODULE/NETWORK/STEP/DATABASE) 도형으로 배치하고, 도면符号를 110부터 10씩 증가시켜 부여합니다.' },
      { title: '엣지 필터링', detail: 'INPUT/OUTPUT 연결, 셀프 루프, 중복 엣지, 유효하지 않은 컴포넌트 ID 연결을 모두 제거합니다.' },
      { title: '도2 — 방법 흐름도', detail: '처리 단계를 step_number 순으로 정렬해 S210부터 10씩 증가하는 도면符号의 박스 노드로 변환, 단계 간 화살표만 연결합니다.' },
      { title: 'Graphviz 렌더링', detail: 'dot.render()로 PNG(300dpi)로 렌더링하고, S3 버킷이 설정되어 있으면 S3에 업로드, 없으면 Django media 폴더로 이동합니다.' },
    ],
    specs: [
      { label: '생성 방식', value: 'Graphviz DOT (LLM 미사용, 순수 템플릿)' },
      { label: '도면 종류', value: 'BLOCK_DIAGRAM(도1), FLOWCHART(도2)' },
      { label: '폰트', value: 'NanumGothic' },
      { label: '해상도', value: '300dpi PNG' },
      { label: '저장 위치', value: 'S3 (설정 시) 또는 Django MEDIA_ROOT' },
    ],
    sourceFiles: ['agents/drawing_agent.py', 'backend/fastapi/routers/drawings.py'],
  },
  {
    slug: 'specification',
    name: '명세서 작성',
    tagline: '7개 핵심 항목을 검증·재작성 루프까지 거쳐 자동 완성합니다',
    description:
      '기술분야부터 발명의 상세한 설명까지 명세서 필수 7개 항목을 LLM으로 생성한 뒤, 누락·IPC 코드 노출·선행기술조사 보고서체 표현 등을 규칙 기반으로 검증합니다. 검증에 실패하면 같은 LLM이 지적된 부분만 고쳐 최대 2회까지 재작성합니다.',
    steps: [
      { title: '재료 수집', detail: '청구항·도면·발명 요약 데이터를 모아 SpecificationMaterial을 구성합니다.' },
      { title: '7개 섹션 동시 생성', detail: 'technical_field·background_art·problem_to_solve·means_for_solving·effects·brief_description_of_drawings·detailed_description을 한 번에 생성합니다.' },
      { title: '규칙 기반 검증', detail: '필수 섹션 누락, IPC 코드 직접 노출, 선행기술조사 보고서식 표현, 문단 수 초과 등을 정규식으로 점검합니다.' },
      { title: '실패 시 재작성', detail: '검증 실패 사유를 그대로 프롬프트에 포함해 같은 LLM에게 재작성을 요청, 최대 2회 반복합니다.' },
      { title: '용어 정규화', detail: '재작성 후에도 명세서 전체의 용어 표기를 통일하고, 새로 발생한 이슈가 있으면 경고로 남깁니다.' },
    ],
    specs: [
      { label: 'LLM', value: 'gpt-5.1 (OPENAI_SPEC_MODEL 환경변수로 교체 가능)' },
      { label: 'Temperature', value: '0.1' },
      { label: '생성 섹션', value: '7개 (기술분야~상세한 설명)' },
      { label: '최대 재작성', value: '2회 (max_repair_attempts)' },
      { label: '검증 실패 시 정책', value: 'status=ok로 진행, warnings에 이슈 기록 (MVP 정책)' },
    ],
    sourceFiles: ['agents/specification/specification_agent.py', 'agents/specification/spec_helpers.py', 'backend/fastapi/routers/specification.py'],
  },
]