# Specification Agent 품질 평가

이 폴더는 일반 단위 테스트가 아니라, Specification Agent가 생성한 **발명의 설명**의
실시가능성·청구항 뒷받침·근거 충실성·명확성·기술분야별 충실도를 점수화하는 평가 프로그램입니다.
기존 `tests/`와 별도로 실행하며 기본 pytest 실행에는 포함되지 않습니다.

## 평가 범위

Specification Agent가 생성하는 다음 7개 섹션만 평가합니다.

1. 기술분야
2. 배경기술
3. 해결하려는 과제
4. 과제의 해결수단
5. 발명의 효과
6. 도면의 간단한 설명
7. 발명을 실시하기 위한 구체적인 내용

청구항 문장 자체의 형식적 명확성, 신규성, 진보성, 침해 여부는 평가하지 않습니다. 입력 청구항이
발명의 설명에 의해 뒷받침되고 통상의 기술자가 청구된 기술을 실시할 수 있는지는 평가합니다.

## 파일 역할

- `rubric.py`: 버전이 고정된 100점 평가표와 합격 기준
- `schemas.py`: case, Judge 응답, 최종 리포트의 Pydantic 계약
- `judge.py`: 원본 입력과 생성 명세서를 비교하는 별도 LLM Judge
- `run_eval.py`: 명세서 생성, 기계적 검사, Judge 호출, 점수 계산과 리포트 저장
- `cases/*.json`: 실제 Specification Agent 입력 형태를 사용하는 평가 사례

## 점수와 합격 기준

| 평가 항목 | 배점 | 필수 최저점 |
|---|---:|---:|
| 실시가능성 | 40 | 32 |
| 청구항 뒷받침 | 25 | 20 |
| 입력 근거 충실성 | 15 | 12 |
| 명확성·일관성 | 10 | - |
| 기술분야별 충실도 | 10 | - |

총점 80점 이상, 핵심 항목 최저점 충족, 중대 실패 없음, Judge 신뢰도 `medium` 이상이어야 통과합니다.

## 실행

API를 호출하지 않고 case 형식만 검사합니다.

```bash
.venv/bin/python -m evals.specification.run_eval \
  --case evals/specification/cases/general_device.json \
  --dry-run
```

Specification Agent로 새 명세서를 생성한 뒤 Judge로 평가합니다. `.env`의 `OPENAI_API_KEY`를 사용합니다.
이 명령을 직접 실행했을 때만 평가하며, 운영 애플리케이션에서 명세서가 생성될 때마다 자동 실행되지는
않습니다. 한 번 실행할 때 명세서 한 건을 생성한 뒤 같은 결과를 한 번 평가합니다.

```bash
OPENAI_SPEC_MODEL=gpt-4o \
OPENAI_JUDGE_MODEL=gpt-4o \
.venv/bin/python -m evals.specification.run_eval \
  --case evals/specification/cases/general_device.json \
  --api-timeout 120
```

실행 중에는 명세서 생성, 기계적 검사, LLM Judge의 세 단계와 각 소요 시간이 출력됩니다. 생성 및 Judge
API는 기본적으로 각각 120초의 제한 시간을 사용합니다. 느린 모델을 사용하는 경우 `--api-timeout 300`
처럼 늘릴 수 있으며, `OPENAI_API_TIMEOUT` 환경변수로도 기본값을 지정할 수 있습니다.

기본 실행은 결과를 터미널에만 표시하고 파일을 생성하지 않습니다. 항목별 점수, 최종 판단, Agent 문제,
입력 자료 부족 및 Judge 요약이 출력됩니다.

가능하면 생성 모델과 Judge 모델을 다르게 설정하십시오. 같은 모델을 쓰더라도 생성 프롬프트와 평가
프롬프트는 분리되지만, 서로 다른 모델을 사용하면 자기 선호 편향을 줄이는 데 도움이 됩니다.

이미 저장한 Agent 결과만 평가할 수도 있습니다. candidate는 Agent 원본 출력, FastAPI의 `result`,
또는 과거 평가 리포트의 `specification` 형태를 허용합니다.

```bash
.venv/bin/python -m evals.specification.run_eval \
  --case evals/specification/cases/general_device.json \
  --candidate /path/to/specification.json
```

결과를 파일로 보관해야 할 때만 `--save`를 사용합니다.

```bash
.venv/bin/python -m evals.specification.run_eval \
  --case evals/specification/cases/general_device.json \
  --api-timeout 120 \
  --save
```

이 경우 기존 Git ignore 대상인 `.cache/specification-evals/`에 candidate JSON과 최종 JSON·Markdown
리포트를 저장합니다. Judge가 실패하더라도 생성 결과를 재사용할 수 있도록 candidate 체크포인트는
Judge 호출 전에 먼저 저장됩니다.

## 실제 입력 형태와 청구항 평가

case의 `agent_state`는 `run_specification_agent()`가 실제로 받는 구조를 그대로 사용합니다. 운영 경로의
청구항은 `text`는 있지만 `elements`가 없는 경우가 있으므로 기존 `support_matrix`만으로 뒷받침 여부를
판정하지 않습니다. LLM Judge가 독립항 원문을 직접 구성요소와 기술적 관계로 분해한 뒤 발명의 설명과
대응시킵니다. `support_matrix`가 존재하면 기계적 보조자료로 함께 사용합니다.

## 결과 해석 주의

평가는 제공된 출원일, 통상의 기술자 프로필, 입력 자료와 버전 고정 평가표를 기준으로 합니다. 입력에
필요한 기술 정보가 없다면 Judge는 이를 `input_gaps`로, 입력에는 있지만 명세서가 사용하지 못했다면
`agent_issues`로 구분합니다. 결과는 개발 단계의 품질 지표이며 변리사나 법률 전문가의 의견을 대체하지
않습니다.
