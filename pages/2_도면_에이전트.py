import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="도면 에이전트 | PatentAI",
    page_icon="⚖️",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500;600&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #F5F4F1;
    font-family: 'Noto Sans KR', sans-serif;
    color: #1A1A2E;
}

header[data-testid="stHeader"] { display: none; }

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

.page-kicker {
    color: #C9A84C;
    letter-spacing: .3em;
    font-size: .72rem;
    font-weight: 700;
    margin-bottom: .6rem;
}

.page-title {
    font-family: 'Noto Serif KR', serif;
    font-size: 2.2rem;
    font-weight: 300;
    color: #111128;
    margin-bottom: .5rem;
}

.page-sub {
    color: #666;
    line-height: 1.8;
    font-size: .95rem;
    margin-bottom: 2rem;
}

.divider {
    width: 40px;
    height: 2px;
    background: #C9A84C;
    margin-bottom: 1.5rem;
}

.grade-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    color: white;
}

.stButton > button {
    border-radius: 0;
    background: #111128;
    color: #C9A84C;
    border: 1px solid #111128;
    padding: .7rem 2.2rem;
    font-weight: 700;
}

.stButton > button:hover {
    background: #C9A84C;
    color: #111128;
    border-color: #C9A84C;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-kicker">DRAWING AGENT</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">특허 도면 자동 생성</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">발명 명세서 텍스트를 입력하면 블록도, 흐름도 등 특허청 실무 수준의 SVG 도면을 자동 생성합니다.</div>',
    unsafe_allow_html=True,
)

# ── 입력 폼 ──────────────────────────────────────────────
with st.form("drawing_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        invention_text = st.text_area(
            "발명 명세서 텍스트",
            height=260,
            placeholder=(
                "예시)\n"
                "본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것이다.\n"
                "입력부(110)는 이미지를 입력받는다.\n"
                "전처리부(120)는 이미지를 전처리한다.\n"
                "CNN 모델부(130)는 분류를 수행한다.\n"
                "저장부(140)는 결과를 저장한다.\n\n"
                "도 1은 전체 구성도이다.\n"
                "도 2는 처리 흐름도이다.\n\n"
                "부호의 설명\n110: 입력부\n120: 전처리부\n130: CNN 모델부\n140: 저장부"
            ),
        )
    with col2:
        app_num = st.text_input("출원번호 / 식별자", value="DRAWING-001",
                                help="결과 파일 저장 폴더명으로 사용됩니다.")
        export_png = st.checkbox("PNG 변환", value=False,
                                 help="cairosvg 또는 ImageMagick 필요")
        auto_repair = st.checkbox("자동 품질 보정", value=True)
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("도면 생성", use_container_width=True, type="primary")

# ── 실행 ─────────────────────────────────────────────────
if submitted:
    if not invention_text.strip():
        st.warning("발명 명세서 텍스트를 입력해주세요.")
        st.stop()

    with st.spinner("도면 분석 및 SVG 생성 중... (30초~1분 소요)"):
        try:
            from drawing_agent import generate_all_drawings
            results = generate_all_drawings(
                invention_text=invention_text,
                app_num=app_num.strip() or "DRAWING-001",
                output_dir="drawing_analysis",
                export_svg=True,
                export_png=export_png,
                auto_repair=auto_repair,
            )
        except Exception as e:
            st.error(f"도면 생성 오류: {e}")
            st.stop()

    if not results:
        st.error("도면 생성에 실패했습니다.")
        st.stop()

    st.success(f"✅ 도면 {len(results)}장 생성 완료")
    st.markdown("---")

    cols = st.columns(min(len(results), 2))
    for i, dr in enumerate(results):
        with cols[i % 2]:
            grade_color = "#27ae60" if dr.quality_grade == "A" else "#f39c12" if dr.quality_grade == "B" else "#e74c3c"
            st.markdown(f"**{dr.fig_number} — {dr.diagram_title}**")
            st.markdown(
                f'<span class="grade-badge" style="background:{grade_color}">'
                f'{dr.quality_grade}등급 {dr.quality_score}점</span>',
                unsafe_allow_html=True,
            )

            svg_path = Path(dr.svg_path)
            if svg_path.exists():
                st.components.v1.html(svg_path.read_text(encoding="utf-8"), height=480, scrolling=True)

                with open(svg_path, "rb") as f:
                    st.download_button(
                        label=f"⬇ {dr.fig_number} SVG 다운로드",
                        data=f.read(),
                        file_name=svg_path.name,
                        mime="image/svg+xml",
                        use_container_width=True,
                    )

            png_path = Path(dr.png_path) if dr.png_path else Path("")
            if png_path.exists():
                with open(png_path, "rb") as f:
                    st.download_button(
                        label=f"⬇ {dr.fig_number} PNG 다운로드",
                        data=f.read(),
                        file_name=png_path.name,
                        mime="image/png",
                        use_container_width=True,
                    )
