"""Drawing Agent 최소 입출력 예시 + schema validation 확인.

실행: python -m agents.drawing.example_io
"""

from agents.schemas.drawing import DrawingAgentOutput, FigureDraft, ReferenceNumeral

EXAMPLE_INPUT_STATE = {
    "consultation": {
        "invention_title": "스마트 재고 관리 시스템",
        "problem": "수작업 재고 집계로 인한 오류와 지연",
        "solution": "IoT 센서와 AI 예측 모델을 결합한 자동 재고 추적",
        "components": [
            {"name": "IoT 센서 모듈", "role": "실시간 재고 수량 감지"},
            {"name": "AI 예측 엔진", "role": "소비 패턴 분석 및 발주 예측"},
            {"name": "중앙 관리 서버", "role": "데이터 수집·처리·저장"},
        ],
        "process_steps": [
            {"order": 1, "name": "센서 데이터 수집", "description": "각 진열대 IoT 센서가 수량 변화 감지"},
            {"order": 2, "name": "AI 분석", "description": "수집 데이터를 AI 모델로 분석"},
            {"order": 3, "name": "알림 발송", "description": "임계치 도달 시 담당자에게 자동 알림"},
        ],
    }
}

EXAMPLE_OUTPUT = {
    "status": "ok",
    "summary": "도면 2개 생성 완료 (평균 82점)",
    "figures": [
        {
            "fig_no": "1",
            "title": "스마트 재고 관리 시스템 구성도",
            "type": "system_architecture",
            "components": ["IoT 센서 모듈", "AI 예측 엔진", "중앙 관리 서버"],
            "description": "전체 시스템 블록 구성도",
        },
        {
            "fig_no": "2",
            "title": "재고 관리 처리 흐름도",
            "type": "flowchart",
            "components": ["센서 데이터 수집", "AI 분석", "알림 발송"],
            "description": "데이터 처리 흐름도",
        },
    ],
    "reference_numerals": [
        {"number": "100", "label": "IoT 센서 모듈", "description": "실시간 재고 수량 감지", "component_id": "100"},
        {"number": "110", "label": "AI 예측 엔진", "description": "소비 패턴 분석 및 발주 예측", "component_id": "110"},
        {"number": "120", "label": "중앙 관리 서버", "description": "데이터 수집·처리·저장", "component_id": "120"},
    ],
    "drawing_notes": [
        "총 2개 도면 생성",
        "평균 품질 점수: 82.0점",
        "참조부호 3개",
    ],
}

EXAMPLE_FALLBACK = {
    "status": "failed",
    "summary": "도면 생성 실패 — hard fallback",
    "figures": [],
    "reference_numerals": [],
    "drawing_notes": [],
}


def validate_example() -> None:
    out = DrawingAgentOutput(**EXAMPLE_OUTPUT)
    assert out.status == "ok"
    assert len(out.figures) == 2
    assert out.figures[0].fig_no == "1"
    assert len(out.reference_numerals) == 3
    assert out.reference_numerals[0].number == "100"

    fallback = DrawingAgentOutput(**EXAMPLE_FALLBACK)
    assert fallback.status == "failed"
    assert fallback.figures == []

    print("DrawingAgentOutput schema validation: PASS")
    print(f"  figures: {len(out.figures)}개")
    print(f"  reference_numerals: {len(out.reference_numerals)}개")
    print(f"  drawing_notes: {out.drawing_notes}")
    print(f"  fallback status: {fallback.status}")


if __name__ == "__main__":
    validate_example()
