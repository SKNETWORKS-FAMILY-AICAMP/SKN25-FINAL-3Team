import json
import sys
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

import agents.composer.composer_agent as composer_agent
from agents.composer.composer_agent import run_composer_agent


st.set_page_config(
    page_title="Composer Agent 테스트",
    page_icon="🧪",
    layout="wide",
)


MOCK_SUMMARY = (
    "본 발명은 카드 승인 단말 시스템과 이를 이용한 카드 관리 방법에 관한 것으로서, "
    "카드 속성 정보와 속성 변경 정보를 데이터베이스 관리부를 통해 관리하고, "
    "최종 카드 속성 정보를 생성하여 카드 거래 처리를 수행할 수 있도록 한다."
)


def load_uploaded_json(uploaded_json):
    if uploaded_json is None:
        return None
    return json.loads(uploaded_json.getvalue().decode("utf-8"))


def resolve_path(path_value):
    if not path_value:
        return None

    path = Path(path_value)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def copy_uploaded_images(uploaded_images):
    temp_dir = tempfile.TemporaryDirectory(prefix="composer_images_")
    copied = {}

    for uploaded in uploaded_images or []:
        dest_path = Path(temp_dir.name) / uploaded.name
        dest_path.write_bytes(uploaded.getvalue())
        copied[uploaded.name] = dest_path

    return temp_dir, copied


def patch_images_to_state(state, uploaded_images):
    temp_dir, copied = copy_uploaded_images(uploaded_images)
    drawings = state.get("drawings") or {}
    figures = drawings.get("figures") if isinstance(drawings.get("figures"), list) else []

    for figure in figures:
        if not isinstance(figure, dict):
            continue

        current_path = figure.get("image_path") or figure.get("png_path") or figure.get("svg_path")
        if not current_path:
            continue

        basename = Path(str(current_path)).name
        if basename in copied:
            figure["image_path"] = str(copied[basename])
            figure["png_path"] = str(copied[basename])
            figure["svg_path"] = str(copied[basename])

    state["drawings"] = drawings
    state["_composer_uploaded_images_tempdir"] = temp_dir
    return state


def mock_generate_abstract_from_claim_1(*args, **kwargs):
    return MOCK_SUMMARY


def summarize_state(state):
    summary = state.get("summary") or {}
    claims = state.get("claims") or {}
    drawings = state.get("drawings") or {}
    specification = state.get("specification") or {}
    prior_art = state.get("prior_art") or {}
    document_links = state.get("document_links") or {}
    invention_graph = state.get("invention_graph") or {}

    reference_map = document_links.get("reference_numeral_map")
    if not isinstance(reference_map, dict):
        reference_map = {}

    return {
        "발명명칭": summary.get("project_name") or summary.get("title") or state.get("title") or "(미지정)",
        "청구항 개수": len(claims.get("draft_claims", [])) if isinstance(claims.get("draft_claims"), list) else 0,
        "도면 개수": len(drawings.get("figures", [])) if isinstance(drawings.get("figures"), list) else 0,
        "발명의 설명 섹션 존재 여부": bool(specification),
        "prior_art 후보 개수": len(prior_art) if isinstance(prior_art, dict) else 0,
        "document_links.reference_numeral_map 개수": len(reference_map),
        "invention_graph 존재 여부": bool(invention_graph),
    }


def check_image_paths(state):
    drawings = state.get("drawings") or {}
    figures = drawings.get("figures") if isinstance(drawings.get("figures"), list) else []

    existing = 0
    missing = []
    for figure in figures:
        if not isinstance(figure, dict):
            continue
        image_path = figure.get("image_path") or figure.get("png_path") or figure.get("svg_path")
        resolved = resolve_path(image_path)
        if resolved and resolved.exists():
            existing += 1
        else:
            missing.append(str(image_path or "(경로 없음)"))
    return existing, missing


def validate_markdown(markdown_text):
    checks = []
    text = markdown_text or ""

    checks.append(("요약 섹션 존재", "## 요약" in text))
    checks.append(("대표도 섹션 존재", "## 대표도" in text))
    checks.append(("청구항 섹션 존재", "## 청구항" in text))
    checks.append(("발명의 설명 섹션 존재", "## 발명의 설명" in text))
    checks.append(("도면 섹션 존재", "## 도면" in text))
    checks.append(("금지 항목 미포함", "【발명의 설명】" not in text and "【발명의 명칭】" not in text))

    if "## 발명의 설명" in text:
        intro_idx = text.find("## 발명의 설명")
        after_intro = text[intro_idx:]
        first_heading = next(
            (
                line.strip().lstrip("#").strip()
                for line in after_intro.splitlines()
                if line.strip().startswith("###") or line.strip().startswith("##")
            ),
            "",
        )
        checks.append(("발명의 설명 다음이 【기술분야】가 아님", first_heading == "【기술분야】"))
    else:
        checks.append(("발명의 설명 다음이 【기술분야】가 아님", False))

    return checks


def extract_final_package(result):
    if isinstance(result, dict) and "final_package" in result:
        return result["final_package"]
    return result


def main():
    st.title("Composer Agent 테스트")
    st.markdown(
        """
        실제 특허 PDF 기반 PatentAgentState JSON을 사용하여 Composer Agent가 `final_package`, `rendered_markdown`, 그리고 실제 `.docx` 파일을 정상 생성하는지 확인합니다.

        > 실행 방법: `streamlit run agents/composer/composer_test_app.py`
        """
    )

    uploaded_json = st.file_uploader("PatentAgentState JSON 업로드", type=["json"])
    uploaded_images = st.file_uploader(
        "도면 이미지 업로드 (선택 사항, 업로드하면 경로를 자동으로 연결합니다)",
        type=["png", "jpg", "jpeg", "svg", "bmp", "gif", "tif", "tiff"],
        accept_multiple_files=True,
    )

    if uploaded_json is None:
        st.warning("JSON 파일을 먼저 업로드해 주세요.")
        st.stop()

    try:
        state = load_uploaded_json(uploaded_json)
    except Exception as exc:
        st.error("JSON 파싱 중 오류가 발생했습니다.")
        st.exception(exc)
        st.stop()

    if uploaded_images:
        state = patch_images_to_state(state, uploaded_images)
        st.success(f"{len(uploaded_images)}개의 도면 이미지를 업로드했습니다.")

    st.subheader("State 요약")
    summary = summarize_state(state)
    for label, value in summary.items():
        st.write(f"- **{label}**: {value}")

    st.subheader("이미지 경로 확인")
    existing_images, missing_images = check_image_paths(state)
    st.write(f"존재하는 이미지 개수: {existing_images}")
    st.write(f"누락된 이미지 개수: {len(missing_images)}")
    if missing_images:
        st.warning("다음 이미지 경로가 누락되었습니다.")
        for path in missing_images:
            st.write(f"- {path}")
    else:
        st.success("모든 이미지 경로가 확인되었습니다.")

    use_mock_summary = st.checkbox(
        "LLM 요약 호출 대신 테스트용 요약 사용",
        value=True,
        help="테스트 단계에서는 기본적으로 mock 요약을 사용합니다.",
    )

    if st.button("Composer 실행", type="primary"):
        original_generate = composer_agent.generate_abstract_from_claim_1
        try:
            if use_mock_summary:
                composer_agent.generate_abstract_from_claim_1 = mock_generate_abstract_from_claim_1

            result = run_composer_agent(state)
            final_package = extract_final_package(result)

            if not isinstance(final_package, dict):
                raise TypeError("final_package는 dict 형태여야 합니다.")

            st.success("Composer 실행 성공")

            st.subheader("실행 결과")
            st.write(f"- final_package 존재 여부: 예")
            st.write(f"- title: {final_package.get('title')}")
            st.write(f"- abstract: {final_package.get('abstract', '')[:300]}")
            st.write(f"- rendered_docx_path: {final_package.get('rendered_docx_path')}")

            if final_package.get("composer_notes"):
                st.write("- composer_notes")
                for note in final_package.get("composer_notes", []):
                    st.write(f"  - {note}")

            if final_package.get("unresolved_items"):
                st.write("- unresolved_items")
                for item in final_package.get("unresolved_items", []):
                    st.write(f"  - {item}")

            docx_path = final_package.get("rendered_docx_path") or state.get("final_docx_path")
            if docx_path and Path(docx_path).exists():
                with Path(docx_path).open("rb") as fp:
                    st.download_button(
                        label="최종 명세서 Word 다운로드",
                        data=fp.read(),
                        file_name=Path(docx_path).name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
            else:
                st.warning("DOCX 파일이 생성되지 않았거나 경로를 찾을 수 없습니다.")

            rendered_markdown = final_package.get("rendered_markdown")
            if rendered_markdown:
                st.subheader("rendered_markdown 미리보기")
                st.markdown(rendered_markdown)
            else:
                st.warning("rendered_markdown이 없습니다. Composer에서 rendered_markdown 생성 로직을 확인하세요.")

            st.subheader("문서 구조 검증")
            for label, passed in validate_markdown(rendered_markdown):
                if passed:
                    st.write(f"- ✅ {label}")
                else:
                    st.write(f"- ❌ {label}")

        except Exception as exc:
            st.error("Composer 실행 중 오류가 발생했습니다.")
            st.exception(exc)
            st.markdown(
                """
                다음 항목을 확인해 주세요.
                - JSON 경로 문제
                - 이미지 경로 문제
                - OPENAI_API_KEY 미설정(실제 LLM 호출 시)
                - `state["specification"]` 누락
                - `state["claims"]["draft_claims"]` 누락
                - `state["drawings"]["figures"]` 누락
                - Composer import 경로 문제
                """
            )
        finally:
            composer_agent.generate_abstract_from_claim_1 = original_generate

    with st.expander("입력 State 보기"):
        st.json(state)

    with st.expander("Final Package 보기"):
        st.json(extract_final_package(state.get("final_package", {})) if isinstance(state.get("final_package"), dict) else state.get("final_package", {}))


if __name__ == "__main__":
    main()
