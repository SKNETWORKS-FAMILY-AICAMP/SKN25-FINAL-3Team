"""도면 에이전트 테스트 앱.

실행:
    python -m agents.drawing.drawing_test_app
"""

from agents.drawing.drawing_agent import generate_all_drawings

SAMPLE_TEXT = """
본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것이다.

사용자 단말기(100)는 이미지를 전송한다.
입력부(110)는 이미지를 입력받는다.
전처리부(120)는 이미지를 전처리한다.
이미지가 유효한지 여부를 판단한다.
유효하지 않은 경우 오류를 반환한다.
CNN 모델부(130)는 전처리된 이미지를 분류한다.
저장부(140)는 분석 결과를 저장한다.
출력부(150)는 분류 결과를 출력한다.

도 1은 이미지 분류 시스템의 전체 구성도이다.
도 2는 이미지 분류 방법의 처리 흐름도이다.
"""


def main():
    print("=" * 50)
    print("도면 에이전트 테스트")
    print("=" * 50)

    results = generate_all_drawings(
        invention_text=SAMPLE_TEXT,
        app_num="TEST-DRAWING",
        output_dir="drawing_analysis",
        export_svg=True,
        export_png=False,
    )

    print(f"\n생성된 도면: {len(results)}개")
    for r in results:
        print(f"  - {r.fig_number}: {r.quality_score}점/{r.quality_grade}등급 | {r.diagram_type}")

    assert len(results) >= 2, "도면 2개 이상 생성 실패"
    assert all(r.quality_score >= 75 for r in results), "품질 기준(75점) 미달"
    print("\n✅ 테스트 통과")


if __name__ == "__main__":
    main()
