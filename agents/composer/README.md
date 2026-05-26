# Composer Agent

## 목적

Composer Agent는 각 에이전트가 state에 저장한 산출물을 모아 최종 특허 명세서 Word 문서(.docx)로 조립하는 최종 조립 Agent입니다.

Composer는 새로운 특허 내용을 처음부터 작성하는 Agent가 아닙니다.
요약을 제외한 청구항, 발명의 설명, 도면은 각 Agent의 결과물을 최대한 그대로 사용합니다.

## 최종 문서 순서

최종 Word 문서 순서는 반드시 다음과 같습니다.

1. 요약
2. 대표도
3. 청구항
4. 발명의 설명
5. 도면

특허청 명세서 양식은 전체 문서 순서가 아니라, 발명의 설명 내부 소제목을 정리하기 위한 참고 기준으로만 사용합니다.

## 발명의 설명 작성 규칙

청구항이 끝난 뒤 “발명의 설명” 섹션을 시작합니다.

발명의 설명 섹션에서는 아래 항목을 사용하지 않습니다.

- 【발명(고안)의 설명】
- 【발명(고안)의 명칭】

발명의 설명은 반드시 아래처럼 시작합니다.

발명의 설명

【기술분야】

이후 소제목은 다음 순서를 따릅니다.

1. 【기술분야】
2. 【발명(고안)의 배경이 되는 기술】
3. 【발명(고안)의 내용】
4. 【해결하려는 과제】
5. 【과제의 해결 수단】
6. 【발명(고안)의 효과】
7. 【도면의 간단한 설명】
8. 【발명(고안)을 실시하기 위한 구체적인 내용】

## 파일 구조

agents/composer/
  __init__.py
  README.md
  composer_agent.py
  adapters.py
  abstract_generator.py
  docx_writer.py
  validators.py
  prompts.py

각 파일 설명:

- composer_agent.py: 전체 실행 흐름 오케스트레이션
- adapters.py: state 구조 차이를 흡수하는 getter/fallback 함수
- abstract_generator.py: 청구항 1항 기반 요약문 LLM 생성
- prompts.py: 요약 생성 프롬프트
- docx_writer.py: Word 문서 생성 및 이미지 삽입
- validators.py: Composer 입력값 검증
- README.md: Composer Agent 구조 및 작업 규칙 문서화

## 주요 state 입력값

Composer는 다음 state 값을 우선 사용합니다.

- claim_1_text
- claims_text
- claims
- specification_sections
- specification
- drawings
- drawing_image_paths

도면 정보는 다음 형식을 권장합니다.

drawings = [
    {
        "figure_no": "도 1",
        "description": "도 1은 ...",
        "image_path": "outputs/drawings/fig_1.png",
        "png_path": "outputs/drawings/fig_1.png",
        "svg_path": "outputs/drawings/fig_1.svg"
    }
]

Word 삽입 안정성을 위해 PNG 경로를 image_path 또는 png_path에 저장하는 것을 권장합니다.

## 출력 state

run_composer_agent(state) 실행 후 다음 값이 추가됩니다.

- state["abstract_text"]
- state["representative_drawing_path"]
- state["final_docx_path"]
- state["final_package"]["rendered_docx_path"]
- state["final_package"]["abstract_text"]
- state["final_package"]["representative_drawing_path"]
- state["final_package"]["sections_order"]

## 요약 생성 규칙

요약은 청구항 1항을 기반으로 LLM이 생성합니다.

규칙:

- 청구항 1항의 기술적 구성을 유지
- 없는 구성요소 생성 금지
- 없는 효과 생성 금지
- 권리범위 축소 금지
- 청구항 문장을 그대로 복사하지 않음
- “본 발명은 ...에 관한 것으로서” 문체 사용
- 1문단 또는 2문단 작성
- 특허 명세서 요약문에 맞는 문체 사용

환경변수:

- COMPOSER_MODEL: 요약 생성 모델명, 기본값 gpt-4o
- OPENAI_API_KEY: OpenAI API 키

## 이미지 처리 규칙

Word에 직접 삽입 가능한 이미지 형식:

- png
- jpg
- jpeg
- bmp
- gif
- tif
- tiff

SVG는 Word에 직접 삽입하지 않고 안내 문구로 처리합니다.
가능하면 도면 Agent에서 PNG 파일을 생성하고 image_path 또는 png_path에 저장해야 합니다.

## 금지사항

Composer Agent는 아래 작업을 하지 않습니다.

- 청구항을 새로 다시 작성하지 않음
- 발명의 설명을 임의로 대폭 수정하지 않음
- 도면 내용을 재해석하지 않음
- 없는 선행기술문헌을 추가하지 않음
- 없는 효과를 새로 만들지 않음
- 특허청 양식의 전체 순서를 따라 발명의 설명을 청구항보다 먼저 배치하지 않음
- “【발명(고안)의 설명】”을 넣지 않음
- “【발명(고안)의 명칭】”을 넣지 않음

## 검증 항목

Composer 구현 후 아래 항목을 확인합니다.

- docx가 실제 생성되는지
- 문서 순서가 요약 → 대표도 → 청구항 → 발명의 설명 → 도면인지
- “【발명(고안)의 설명】”이 포함되지 않는지
- “【발명(고안)의 명칭】”이 포함되지 않는지
- “발명의 설명” 다음 첫 소제목이 “【기술분야】”인지
- claims_text에 이미 “【청구범위】”가 있어도 중복되지 않는지
- drawing_image_paths만 있어도 마지막 도면 섹션에 도면이 들어가는지
- SVG만 있는 경우 Word 삽입 실패 대신 안내 문구가 들어가는지
