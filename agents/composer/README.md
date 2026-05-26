# Composer Agent

## 목적

Composer Agent는 각 에이전트가 state에 저장한 산출물을 모아 최종 특허 명세서 Word 문서(.docx)로 조립하는 최종 조립 Agent입니다.

Composer는 새로운 특허 내용을 처음부터 작성하는 Agent가 아닙니다.
요약을 제외한 청구항, 발명의 설명, 도면은 각 Agent의 결과물을 최대한 그대로 사용합니다.

## 현재 폴더 구성

agents/composer/
  __init__.py
  README.md
  composer_agent.py
  composer_test_app.py
  adapters.py
  abstract_generator.py
  docx_writer.py
  validators.py
  prompts.py

### 각 파일의 역할

- `composer_agent.py`: `run_composer_agent(state)`를 통해 실제 DOCX 생성과 `final_package` 생성을 담당합니다.
- `composer_test_app.py`: Streamlit 기반 개발용 검증 화면으로, JSON 업로드, 이미지 업로드, Composer 실행, DOCX 다운로드, 결과 검증을 지원합니다.
- `adapters.py`: state 구조 차이를 흡수하는 getter / fallback 함수입니다.
- `abstract_generator.py`: 청구항 1항을 기반으로 요약문을 생성하고, 생성 결과를 정리(cleanup)합니다.
- `prompts.py`: 요약문 생성용 시스템 프롬프트를 정의합니다.
- `docx_writer.py`: Word 문서 생성, 청구항 렌더링, 도면 렌더링, 마크다운 렌더링을 담당합니다.
- `validators.py`: Composer 입력값 검증을 담당합니다.
- `README.md`: Composer Agent의 현재 구조와 동작 규칙을 문서화합니다.

## 현재 동작 요약

### 1. 최종 문서 순서

최종 Word 문서 순서는 다음과 같습니다.

1. 요약
2. 대표도
3. 청구항
4. 발명의 설명
5. 도면

특허청 명세서 양식은 전체 문서 순서가 아니라, 발명의 설명 내부 소제목을 정리하기 위한 참고 기준으로만 사용합니다.

### 2. 발명의 설명 작성 규칙

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

### 3. 요약 생성 규칙

요약은 청구항 1항을 기반으로 LLM이 생성합니다.

현재 요약 흐름은 아래와 같습니다.

- `get_claim_1_text()`로 청구항 1항을 추출합니다.
- `get_first_non_empty()`로 문제 / 해결수단 / 효과를 추출합니다.
- `generate_abstract_from_claim_1()`이 LLM을 호출합니다.
- `clean_abstract_text()`가 생성 결과를 정리합니다.

정리 규칙:

- `【요약】` 표기를 제거합니다.
- 앞의 `요약` 문자열을 제거합니다.
- 나머지 요약 본문만 유지합니다.

### 4. 현재 요약 프롬프트 정책

현재 `prompts.py`의 요약 프롬프트는 아래 정책을 반영합니다.

- 청구항 1항의 기술적 구성을 유지합니다.
- 청구항 1항을 그대로 복사하지 않습니다.
- 참고 정보는 보조 수단으로만 사용합니다.
- 청구항 1항에 없는 구성요소를 추가하지 않습니다.
- 과장 표현, 마케팅 문구, 설명문, 표제, 불필요한 구분선을 피합니다.
- 출력은 한 문단으로 간결하게 유지합니다.

### 5. 현재 도면 렌더링 정책

현재 `docx_writer.py`의 도면 렌더링은 다음을 보장합니다.

- 마지막 도면 섹션에 도면이 표시됩니다.
- 도면 설명 텍스트를 마크다운에 따로 붙이지 않습니다.
- 도면은 `figure_no` 및 실제 이미지 경로 기준으로 표시됩니다.
- 이미지가 없으면 `이미지 없음`으로 표시합니다.

### 6. 청구항 렌더링 정책

현재 `docx_writer.py`는 청구항 번호를 보존합니다.

- 입력이 `claim_no`를 가진 경우 원래 번호를 유지합니다.
- `claim_no`가 1, 3, 5처럼 비연속이어도 그대로 유지합니다.
- 삭제된 청구항이 존재하더라도 실제 남아 있는 청구항만 렌더링합니다.

## 주요 state 입력값

Composer는 **PatentAgentState 전체를 입력으로 받는다**는 전제를 따른다.

`run_composer_agent(state)`는 다음 입력들을 읽는다.

- `summary`
- `prior_art`
- `claims`
- `drawings`
- `specification`
- `document_links`
- `invention_graph`
- `drafting_options`

`claims.draft_claims`와 `specification`의 섹션은 재작성하지 않고 그대로 최종 문서에 반영합니다.
`document_links`와 `invention_graph`는 대규모 재작성에 쓰지 않고 일관성 점검용으로만 참고합니다.

도면 정보는 다음 형식을 권장합니다.

```python
state["drawings"] = {
    "figures": [
        {
            "figure_no": "도 1",
            "description": "도 1은 ...",
            "image_path": "outputs/drawings/fig_1.png",
            "png_path": "outputs/drawings/fig_1.png",
            "svg_path": "outputs/drawings/fig_1.svg"
        }
    ],
    "reference_numerals": {},
    "drawing_notes": []
}
```

Word 삽입 안정성을 위해 PNG 경로를 `image_path` 또는 `png_path`에 저장하는 것을 권장합니다.

## 출력 state

`run_composer_agent(state)`는 **ComposerAgentOutput와 호환되는 dict를 반환**하며, 동시에 실제 `.docx` 파일을 생성합니다.

반환 구조는 다음과 같은 계약을 따른다.

```python
{
    "status": "ok",
    "summary": "...",
    "warnings": [],
    "notes": [],
    "evidence": [],
    "details": {},
    "title": title,
    "abstract": abstract_text,
    "sections": {...},
    "claims": state["claims"]["draft_claims"],
    "drawings": state["drawings"],
    "specification": state["specification"],
    "prior_art_report": state.get("prior_art", {}),
    "rendered_markdown": rendered_markdown,
    "rendered_docx_path": final_docx_path,
    "rendered_html_path": None,
    "unresolved_items": [],
    "composer_notes": []
}
```

또한 `state["final_package"]`에 동일한 구조를 저장합니다. `agents/graph.py`의 `safe_validate_output()`가 이 반환값을 검증한 뒤 상태에 반영합니다.

## 스트림릿 검증 앱

`composer_test_app.py`는 Composer 동작을 검증하기 위한 개발용 Streamlit 화면입니다.

### 지원 기능

- PatentAgentState JSON 업로드
- 도면 이미지 업로드
- 업로드한 이미지 경로 자동 연결
- Composer 실행
- DOCX 다운로드
- `rendered_markdown` 미리보기
- 문서 구조 검증 결과 표시
- `final_package` 미리보기

### 기본 사용 방법

```bash
streamlit run agents/composer/composer_test_app.py
```

### 테스트 앱 특이사항

- 기본적으로 `LLM 요약 호출 대신 테스트용 요약 사용` 체크박스가 활성화되어 있습니다.
- 실제 LLM 호출을 원하면 체크를 해제하고 `OPENAI_API_KEY`를 설정해야 합니다.
- `.env` 자동 로드를 사용해 OpenAI 키를 주입합니다.

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
가능하면 도면 Agent에서 PNG 파일을 생성하고 `image_path` 또는 `png_path`에 저장해야 합니다.

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

- `docx`가 실제 생성되는지
- `rendered_docx_path`가 실제 생성된 경로인지
- `rendered_markdown`가 전체 문서를 포함하는지
- 문서 순서가 요약 → 대표도 → 청구항 → 발명의 설명 → 도면인지
- “【발명(고안)의 설명】”이 포함되지 않는지
- “【발명(고안)의 명칭】”이 포함되지 않는지
- “발명의 설명” 다음 첫 소제목이 “【기술분야】”인지
- `claims.draft_claims`를 재작성하지 않고 그대로 반영하는지
- `specification`의 7개 섹션을 그대로 반영하는지
- `document_links`와 `invention_graph`가 대규모 재작성에 쓰이지 않고 참고용으로만 사용되는지
- claims_text에서 청구항 1항 추출에 실패할 경우 전체 claims_text를 요약에 넣지 않고 오류를 발생시키는지
- “【청구항1】”, “【청구항 1】”, “【청구항  1】” 형식을 모두 처리하는지
- 문제/해결/효과가 모두 비어 있을 때 “【발명(고안)의 내용】” 제목만 단독으로 들어가지 않는지
- claims_text에 이미 “【청구범위】”가 있어도 중복되지 않는지
- `drawing_image_paths`만 있어도 마지막 도면 섹션에 도면이 들어가는지
- SVG만 있는 경우 Word 삽입 실패 대신 안내 문구가 들어가는지
- 도면 설명이 마크다운에 포함되지 않는지
- 청구항 번호가 원본 번호를 유지하는지
- 요약 결과가 `clean_abstract_text()`를 거친 뒤 정리된 형태로 저장되는지
