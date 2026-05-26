# Specification Agent

이 패키지는 LangGraph 멀티 에이전트 시스템에서 **Composer가 최종 특허 문서에 포함할 발명의 설명 파트 생성**을 담당합니다.
최신 LangGraph MVP의 기본 실행 흐름에서는 **DB를 사용하지 않으며**, 오직 `state`를 통해 에이전트 간 정보를 주고받습니다. 에이전트는 state를 직접 수정하지 않으며, 최종 문서(final_package) 조립도 수행하지 않습니다. 최종 문서는 `composer` 에이전트가 담당합니다.

## 발명의 설명 작성 기준

Specification Agent는 발명의 설명을 크게 3축으로 보고 작성한다.

1. 기술분야 / 배경기술
- 기술분야는 IPC 코드 또는 적용 기술분야 중심의 한 문단으로 작성한다.
- 배경기술은 선행문헌, 종래기술, 기존 문제점 또는 한계를 한 문단으로 작성한다.

2. 해결하고자 하는 과제 / 해결수단 / 효과
- 해결하고자 하는 과제는 종래기술의 문제점과 미충족 수요를 중심으로 작성한다.
- 해결수단은 청구항, 특히 독립항의 내용을 명세서 문체로 바꾸어 작성한다.
- 효과는 종래기술 대비 개선점을 중심으로 작성하되, 제공되지 않은 정량 수치는 만들지 않는다.

3. 도면의 간단한 설명 / 실시예
- 도면의 간단한 설명은 drawings.figures에 있는 도면만 대상으로 작성한다.
- 실시예에 해당하는 detailed_description은 가장 구체적이고 풍부하게 작성한다.
- 가능하면 도면 번호와 참조부호를 사용해 구성요소의 동작을 설명한다.
- 제공되지 않은 도면번호, 참조부호, 구현 세부사항은 만들지 않는다.

## 1. 주요 역할 및 설계

- **섹션 생성**: 기술분야, 배경기술, 해결하려는 과제, 과제의 해결수단, 발명의 효과, 도면의 간단한 설명, 발명을 실시하기 위한 구체적인 내용 등 7개 필수 섹션을 생성합니다.
- **순수 함수적 접근 (Pure Architecture)**: 에이전트는 DB 관련 부수 효과(side effects)가 완전히 제거되어 있습니다. `PatentAgentState`를 입력으로 읽기만 하며, 내부 상태나 DB를 직접 수정하지 않습니다.
- **Output 검증 계약**: 에이전트는 `agents.schemas.specification.SpecificationAgentOutput` 스키마 규격에 맞는 원시 dict 객체를 반환합니다. Graph나 Master 에이전트가 이를 검증하고 state에 병합합니다.
- **Prior Art Details Fallback**: 선행기술 문헌 정보가 `prior_art.candidates`뿐만 아니라 추가 필드(`prior_art.details.candidates_extra`) 등에 나뉘어 있어도 이를 유연하게 병합하여 참조합니다.
- **엄격한 환각 검증**: 참조부호, 공개번호, 미정의 구성요소, 정량 수치 등에 대해 내부 검증(`validate_specification`)을 수행하며, 문제가 있으면 재작성(repair)을 시도합니다. 검증 결과는 `details["validation"]`에 담아 반환합니다.
- **문서 참조 패치(Patch) 생성**: `document_links`를 직접 업데이트하지 않고, 업데이트해야 할 내역을 `details["document_links_patch"]` 및 `details["support_matrix"]`로 반환합니다.

## 2. 필수 환경 변수 및 설정

*   **`OPENAI_API_KEY`**: (필수) 이 환경 변수가 없으면 `RuntimeError`가 발생합니다.
*   **`OPENAI_SPEC_MODEL`**: (선택) 발명의 설명 파트 생성에 사용할 모델을 지정합니다. (기본값: `gpt-5.1`)

## 3. 사용법

### 3.1. 기본 사용 예시 (State 기반, DB 미사용)

현재 MVP에서는 DB 저장 없이 State 기반으로만 동작합니다. 패키지를 임포트해도 DB 연동 코드는 초기화되지 않으므로 DB 설정이 없어도 안전하게 로드됩니다.

```python
import os
from agents.specification import run_specification_agent, SpecificationAgentConfig
from agents.schemas.specification import SpecificationAgentOutput

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 1. 에이전트 실행 (output dict 반환)
config = SpecificationAgentConfig(model="gpt-5.1")
raw_output = run_specification_agent(state, config=config)

# 2. Schema 검증 (Graph/Master 담당 영역)
validated = SpecificationAgentOutput.model_validate(raw_output)

# 3. State 병합 (Graph/Master 담당 영역)
if validated.status == "ok":
    state["specification"] = {
        "technical_field": validated.technical_field,
        "background_art": validated.background_art,
        "problem_to_solve": validated.problem_to_solve,
        "means_for_solving": validated.means_for_solving,
        "effects": validated.effects,
        "brief_description_of_drawings": validated.brief_description_of_drawings,
        "detailed_description": validated.detailed_description,
        "embodiment_notes": validated.details.get("embodiment_notes", []),
    }
    # 이후 details["document_links_patch"]를 state["document_links"]에 병합...
```
### 3.2. 파일 기반 저장소 사용 예시 (신규 마크다운 저장소 기능)

MVP 목표인 파일 기반 명세서 확인 및 다운로드를 위해 `specification_storage.py` 모듈을 제공합니다. 이 모듈을 사용하여 명세서 데이터를 마크다운 파일로 저장하거나 이전에 저장된 파일을 로드할 수 있습니다.

```python
from agents.specification import (
    save_specification,
    load_specification_markdown,
    get_specification_markdown_path
)

# 1. 명세서 데이터를 마크다운 파일로 로컬 디스크에 저장
# 저장 경로: data/specifications/{user_id}/{consultation_idx}/specification.md
# save_json=True일 경우 디버그용 JSON 파일도 함께 생성됩니다.
paths = save_specification(
    user_id="user1",
    consultation_idx=1,
    spec_data=state["specification"],
    save_json=True
)
print("마크다운 저장 완료:", paths["markdown_path"])

# 2. 저장된 명세서 마크다운 파일 로드
markdown_content = load_specification_markdown(
    user_id="user1",
    consultation_idx=1
)
```

## 4. 파일 구성

- `specification_agent.py`: 발명의 설명 섹션 생성을 담당하는 메인 파이프라인. DB 의존성 없이 순수 state만 다루며 output dict만 생성합니다.
- `specification_storage.py`: 생성된 명세서를 특허 형식에 맞게 마크다운 포맷으로 변환하고 파일로 저장/조회하는 마크다운 파일 전용 저장소 유틸리티.
- `spec_helpers.py`: 프롬프트 구성, JSON 파싱, 문단 분리, 환각 검증, 용어 정규화 레코드 생성, patch 및 support_matrix를 생성하는 헬퍼 유틸리티 모음.
- `spec_test_app.py`: 명세서 생성, 마크다운/JSON 로컬 저장 및 실시간 브라우저 다운로드, 과거 생성 이력 로드 및 조회 기능을 제공하는 초프리미엄 사이버 다크 테마 Streamlit 테스트 앱.
- `__init__.py`: 에이전트 실행 및 파일 저장 레이어의 모든 핵심 API를 외부로 노출(export)하는 패키지 진입 파일.

