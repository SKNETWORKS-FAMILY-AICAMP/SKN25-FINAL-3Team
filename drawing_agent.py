# drawing_agent.py - OpenAI 버전
"""
도면 작성 Agent
3.10 발명 내용 기반 도면 구성 요소 추출
3.11 Mermaid / 도면 자동 생성 로직 구현
3.12 도면 출력 포맷 정의
3.13 테스트 및 검증
"""

import os
import glob
import json
import re
import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

# 특허 txt 파일이 있는 폴더 목록 (claim_to_flowchart.py와 동일)
PATENT_DIRS = ["G06F", "G06N", "G06Q", "G06V"]


# ──────────────────────────────────────────
# 3.12 도면 출력 포맷 정의
# ──────────────────────────────────────────

@dataclass
class DrawingComponent:
    component_id: str
    name: str
    component_type: str   # device | process | data | actor
    description: str
    relationships: list


@dataclass
class DrawingResult:
    app_num: str
    diagram_type: str     # flowchart | sequence | classDiagram | stateDiagram
    diagram_title: str
    mermaid_code: str
    components: list
    fig_number: str
    output_path: str


# ──────────────────────────────────────────
# 텍스트 파일 파싱
# ──────────────────────────────────────────

def parse_patent_txt(txt_file: str) -> dict:
    """특허 txt 파일에서 청구범위 + 발명의 상세한 설명 추출"""
    with open(txt_file, "r", encoding="utf-8-sig") as f:
        text = f.read()

    app_num = os.path.basename(txt_file).replace(".txt", "")
    result = {"app_num": app_num, "claims": "", "detail": "", "full": ""}

    # 청구범위 추출
    if "청구범위" in text:
        start = text.find("청구범위")
        end = text.find("발명의 설명", start)
        if end == -1:
            end = text.find("요약", start)
        if end == -1:
            end = start + 3000
        result["claims"] = text[start:end].strip()

    # 발명의 상세한 설명 추출
    for keyword in ["발명의 설명", "발명의 상세한 설명", "상세한 설명"]:
        if keyword in text:
            start = text.find(keyword)
            end = text.find("청구범위", start)
            if end == -1:
                end = start + 5000
            result["detail"] = text[start:end].strip()
            break

    result["full"] = f"[청구범위]\n{result['claims']}\n\n[발명의 상세한 설명]\n{result['detail']}"
    return result


# ──────────────────────────────────────────
# 3.10 발명 내용 기반 도면 구성 요소 추출
# ──────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """당신은 특허 명세서를 분석하여 도면 구성 요소를 추출하는 전문가입니다.

발명 내용을 분석하여 아래 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운 없이 JSON만 출력하세요.

{
  "invention_type": "hardware|software|method|system|hybrid",
  "main_concept": "발명의 핵심 개념 한 줄 요약",
  "recommended_diagrams": [
    {
      "fig_number": "도 1",
      "diagram_type": "flowchart|sequence|classDiagram|stateDiagram",
      "title": "도면 제목",
      "purpose": "이 도면이 표현하는 내용"
    }
  ],
  "components": [
    {
      "component_id": "100",
      "name": "구성요소명",
      "component_type": "device|process|data|actor",
      "description": "역할 설명",
      "relationships": [
        {"target": "200", "label": "관계 설명", "direction": "->"}
      ]
    }
  ],
  "process_flow": ["단계1", "단계2", "단계3"],
  "key_actors": ["행위자1", "행위자2"]
}

특허 도면 작성 원칙:
- 구성요소는 도면부호(100, 200, 300...) 부여
- 방법 발명 → flowchart 우선
- 장치/시스템 발명 → flowchart 또는 classDiagram
- 통신/상호작용 발명 → sequence
- 상태 변화 발명 → stateDiagram
- 도면은 2개 이상 권장 (전체 구성도 + 세부 흐름도)"""


def extract_components(invention_text: str, app_num: str) -> dict:
    """3.10: 발명 내용에서 도면 구성 요소 추출"""
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=3000,
        temperature=0.1,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"특허 출원({app_num}) 발명 내용:\n\n{invention_text[:5000]}"}
        ]
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        print(f"  [경고] JSON 파싱 실패: {app_num}")
        return {}


# ──────────────────────────────────────────
# 3.11 Mermaid 도면 자동 생성 로직
# ──────────────────────────────────────────

MERMAID_SYSTEM_PROMPT = """당신은 특허 도면을 Mermaid 코드로 작성하는 전문가입니다.

규칙:
1. Mermaid 코드만 출력 (마크다운 코드블록, 설명 없이 순수 코드만)
2. 한국어 레이블 사용
3. 공백/특수문자 포함 레이블은 큰따옴표로 감싸기
4. 도면부호(100, 200...) 노드 ID로 사용
5. 최소 4개 이상 노드 포함
6. 계층적이고 명확한 구조

올바른 flowchart 예시:
flowchart TD
    100["입력부"]
    200["전처리부"]
    300["분석부"]
    400["출력부"]
    100 -->|"데이터 전달"| 200
    200 -->|"처리 완료"| 300
    300 -->|"결과"| 400

올바른 sequence 예시:
sequenceDiagram
    participant A as 사용자
    participant B as 서버
    participant C as DB
    A->>B: 요청 전송
    B->>C: 데이터 조회
    C-->>B: 결과 반환
    B-->>A: 응답

올바른 classDiagram 예시:
classDiagram
    class InputUnit {
        +String imageData
        +preprocess()
    }
    class CNNModel {
        +String weights
        +classify()
    }
    InputUnit --> CNNModel : 데이터 전달"""


def generate_mermaid(components_data: dict, diagram_info: dict, app_num: str) -> str:
    """3.11: Mermaid 코드 생성"""
    prompt = f"""특허 출원 {app_num}의 '{diagram_info.get("title")}' 도면을 작성하세요.

발명 정보:
- 유형: {components_data.get('invention_type', '')}
- 핵심: {components_data.get('main_concept', '')}
- 흐름: {json.dumps(components_data.get('process_flow', []), ensure_ascii=False)}
- 행위자: {json.dumps(components_data.get('key_actors', []), ensure_ascii=False)}

구성요소:
{json.dumps(components_data.get('components', []), ensure_ascii=False, indent=2)}

도면 목적: {diagram_info.get('purpose', '')}
다이어그램 타입: {diagram_info.get('diagram_type', 'flowchart')}

{diagram_info.get('diagram_type', 'flowchart')} 형식의 Mermaid 코드만 출력하세요."""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2000,
        temperature=0.1,
        messages=[
            {"role": "system", "content": MERMAID_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    code = response.choices[0].message.content.strip()
    code = re.sub(r"```(?:mermaid)?\s*|\s*```", "", code).strip()
    return code


# ──────────────────────────────────────────
# 3.13 유효성 검증
# ──────────────────────────────────────────

def validate_mermaid(code: str) -> dict:
    """Mermaid 코드 기본 유효성 검사"""
    issues = []
    valid_starts = [
        "flowchart", "graph", "sequenceDiagram",
        "classDiagram", "stateDiagram", "erDiagram", "block-beta"
    ]

    first_line = code.strip().split("\n")[0].strip()
    if not any(first_line.startswith(s) for s in valid_starts):
        issues.append(f"잘못된 다이어그램 타입: {first_line[:40]}")

    if code.count('"') % 2 != 0:
        issues.append("따옴표 불균형")

    # 다이어그램 타입별 노드 카운트
    if "classDiagram" in first_line:
        node_count = len(re.findall(r'class\s+\S+', code))
    elif "sequenceDiagram" in first_line:
        node_count = len(re.findall(r'participant\s+\S+', code))
    elif "stateDiagram" in first_line:
        node_count = len(re.findall(r'state\s+|-->', code))
    else:
        node_count = len(re.findall(r'\[.*?\]|\(.*?\)|{.*?}', code))

    if node_count < 2:
        issues.append(f"노드 수 부족: {node_count}개")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "node_count": node_count,
        "line_count": len(code.split("\n"))
    }


# ──────────────────────────────────────────
# 도면 생성 메인 함수
# ──────────────────────────────────────────

def generate_all_drawings(
    invention_text: str,
    app_num: str,
    output_dir: str = "drawing_analysis"
) -> list:
    """발명 내용으로 전체 도면 생성"""
    results = []

    # 1단계: 구성 요소 추출 (3.10)
    print(f"  [3.10] 구성 요소 추출 중...")
    components_data = extract_components(invention_text, app_num)

    if not components_data:
        print(f"  [오류] 구성 요소 추출 실패")
        return results

    print(f"  → 발명 유형: {components_data.get('invention_type')}")
    print(f"  → 핵심 개념: {components_data.get('main_concept')}")

    # 추천 도면 목록
    recommended = components_data.get("recommended_diagrams", [])
    if not recommended:
        recommended = [{
            "fig_number": "도 1",
            "diagram_type": "flowchart",
            "title": "전체 구성도",
            "purpose": "발명의 전체 구성 및 흐름"
        }]

    # 출력 디렉토리 생성
    app_dir = Path(output_dir) / app_num
    app_dir.mkdir(parents=True, exist_ok=True)

    # 2단계: 각 도면 생성 (3.11)
    for diagram_info in recommended:
        fig_num = diagram_info.get("fig_number", "도 1")
        fig_id = fig_num.replace(" ", "_").replace("도", "fig")

        print(f"  [3.11] {fig_num} '{diagram_info.get('title')}' 생성 중...")
        mermaid_code = generate_mermaid(components_data, diagram_info, app_num)

        validation = validate_mermaid(mermaid_code)
        if not validation["valid"]:
            print(f"  [경고] {validation['issues']}")

        # 3.12 포맷으로 저장
        output_path = str(app_dir / f"{app_num}_{fig_id}.mmd")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"%% {app_num} - {diagram_info.get('title')}\n")
            f.write(f"%% 생성일: {datetime.date.today()}\n\n")
            f.write(mermaid_code)

        result = DrawingResult(
            app_num=app_num,
            diagram_type=diagram_info.get("diagram_type", "flowchart"),
            diagram_title=diagram_info.get("title", ""),
            mermaid_code=mermaid_code,
            components=components_data.get("components", []),
            fig_number=fig_num,
            output_path=output_path
        )
        results.append(result)
        print(f"  [저장] {output_path}")

    # JSON 메타데이터 저장 (3.12)
    meta_path = app_dir / f"{app_num}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "app_num": app_num,
            "invention_type": components_data.get("invention_type"),
            "main_concept": components_data.get("main_concept"),
            "components": components_data.get("components", []),
            "drawings": [asdict(r) for r in results]
        }, f, ensure_ascii=False, indent=2)

    return results


# ──────────────────────────────────────────
# 파일 수집
# ──────────────────────────────────────────

def get_txt_files(limit: Optional[int] = None) -> list:
    """G06X 폴더에서 txt 파일 목록 수집"""
    txt_files = []
    for d in PATENT_DIRS:
        found = glob.glob(f"{d}/*.txt")
        txt_files += found
        print(f"  {d}/: {len(found)}개")
    print(f"  합계: {len(txt_files)}개")
    if limit:
        txt_files = txt_files[:limit]
        print(f"  처리 대상: {len(txt_files)}개 (limit={limit})")
    return txt_files


# ──────────────────────────────────────────
# 3.13 테스트
# ──────────────────────────────────────────

def test_with_sample():
    """샘플 텍스트로 빠른 동작 확인"""
    SAMPLE = """
    본 발명은 딥러닝 기반 이미지 분류 시스템에 관한 것으로,
    입력 이미지를 전처리하는 전처리부(100),
    전처리된 이미지를 분석하는 CNN 모델부(200),
    분류 결과를 출력하는 출력부(300),
    학습 데이터를 관리하는 데이터베이스(400)를 포함한다.

    [청구항 1]
    이미지를 입력받아 전처리하는 단계;
    전처리된 이미지를 CNN 모델에 입력하여 특징을 추출하는 단계;
    추출된 특징으로 이미지를 분류하는 단계;
    분류 결과를 출력하는 단계;를 포함하는 이미지 분류 방법.
    """

    print("=" * 60)
    print("3.13 테스트 - 샘플 데이터")
    print("=" * 60)

    results = generate_all_drawings(
        invention_text=SAMPLE,
        app_num="TEST-001",
        output_dir="drawing_analysis"
    )

    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        v = validate_mermaid(r.mermaid_code)
        status = "✓" if v["valid"] else "✗"
        print(f"  [{r.fig_number}] {r.diagram_title} {status} | 노드: {v['node_count']}개")


def test_with_real_file():
    """실제 특허 파일 1건으로 테스트"""
    txt_files = []
    for d in PATENT_DIRS:
        found = glob.glob(f"{d}/*.txt")
        if found:
            txt_files += found
            break

    if not txt_files:
        print("[경고] G06X 폴더에 txt 파일 없음 → 샘플 테스트로 대체")
        test_with_sample()
        return

    test_file = txt_files[0]
    print("=" * 60)
    print(f"3.13 테스트 - 실제 파일: {test_file}")
    print("=" * 60)

    parsed = parse_patent_txt(test_file)
    if not parsed["claims"] and not parsed["detail"]:
        print("  [경고] 청구범위/설명 추출 실패")
        return

    results = generate_all_drawings(
        invention_text=parsed["full"],
        app_num=parsed["app_num"],
        output_dir="drawing_analysis"
    )

    print(f"\n✅ 생성된 도면: {len(results)}개")
    for r in results:
        v = validate_mermaid(r.mermaid_code)
        status = "✓" if v["valid"] else "✗"
        print(f"  [{r.fig_number}] {r.diagram_title} {status} | 노드: {v['node_count']}개")
        print(f"  저장: {r.output_path}")


# ──────────────────────────────────────────
# 배치 실행 (542건 전체)
# ──────────────────────────────────────────

def run(limit: Optional[int] = None):
    """G06X 폴더 txt 파일 전체 배치 처리"""
    print("=" * 60)
    print("도면 작성 Agent - 배치 실행")
    print("=" * 60)

    print("\n[파일 수집]")
    txt_files = get_txt_files(limit=limit)

    if not txt_files:
        print("[오류] 처리할 파일 없음")
        return

    success, fail, skip = 0, 0, 0

    for i, txt_file in enumerate(txt_files, 1):
        print(f"\n[{i}/{len(txt_files)}] {txt_file}")

        try:
            parsed = parse_patent_txt(txt_file)

            if not parsed["claims"] and not parsed["detail"]:
                print("  [스킵] 청구범위/설명 없음")
                skip += 1
                continue

            results = generate_all_drawings(
                invention_text=parsed["full"],
                app_num=parsed["app_num"],
                output_dir="drawing_analysis"
            )

            if results:
                print(f"  ✅ 완료: {len(results)}개 도면")
                success += 1
            else:
                print(f"  [실패] 도면 생성 안됨")
                fail += 1

        except Exception as e:
            print(f"  [오류] {e}")
            fail += 1

    print("\n" + "=" * 60)
    print(f"배치 완료: 성공 {success} | 실패 {fail} | 스킵 {skip}")
    print(f"결과 저장: drawing_analysis/")
    print("=" * 60)


# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # python drawing_agent.py test       → 샘플 테스트
            test_with_sample()
        elif sys.argv[1] == "real":
            # python drawing_agent.py real       → 실제 파일 1건 테스트
            test_with_real_file()
        elif sys.argv[1] == "run":
            # python drawing_agent.py run        → 전체 배치
            # python drawing_agent.py run 10     → 10건만
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            run(limit=limit)
    else:
        # 인자 없으면 샘플 테스트
        test_with_sample()