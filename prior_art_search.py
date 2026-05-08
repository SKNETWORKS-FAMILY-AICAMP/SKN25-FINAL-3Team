"""
선행기술조사 — 방법 4 구현
흐름: PDF→TXT 추출된 실제 특허 데이터 → 키워드 필터링 → 임베딩 비교 → 유사도 판단 → DB 저장
도면 분석(drawing_analysis/) 결과도 유사도 계산에 반영
IPC 코드: G06N, G06F, G06V, G06Q 전체 검색
"""

import os
import glob
import json
import requests
import numpy as np
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from supabase import create_client

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase      = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

KIPRIS_API_KEY       = os.getenv("KIPRIS_API_KEY")
KIPRIS_BASE_URL      = "http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/patUtiModInfoSearch"
SIMILARITY_THRESHOLD = 0.75
USE_MOCK             = True

IPC_CODES       = ["G06N", "G06F", "G06V", "G06Q"]
TXT_BASE_DIR    = "."
DRAWING_DIR     = "drawing_analysis"


# ──────────────────────────────────────────────
# 1. TXT 파일에서 특허 정보 추출
# ──────────────────────────────────────────────
def extract_claim_from_txt(txt_file: str, ipc: str = "") -> dict | None:
    try:
        with open(txt_file, "r", encoding="utf-8-sig") as f:
            text = f.read()

        claim = ""
        if "청구범위" in text:
            start = text.find("청구범위")
            end   = text.find("발명의 내용", start)
            if end == -1:
                end = start + 3000
            claim = text[start:end].strip()

        title = ""
        for marker in ["(54)", "발명의 명칭"]:
            idx = text.find(marker)
            if idx != -1:
                title = text[idx:idx + 80].replace(marker, "").strip()
                title = title.split("\n")[0].strip()
                break

        abstract = ""
        if "요약" in text:
            abs_start = text.find("요약")
            abstract  = text[abs_start:abs_start + 300].strip()

        app_num = os.path.basename(txt_file).replace(".txt", "")

        return {
            "app_num":  app_num,
            "title":    title or f"특허 {app_num}",
            "abstract": abstract[:200],
            "claim":    claim[:1500],
            "ipc":      ipc,
        }
    except Exception as e:
        print(f"[TXT 추출 오류] {txt_file}: {e}")
        return None


# ──────────────────────────────────────────────
# 2. 특허 검색 (Mock: 로컬 txt / Real: KIPRIS API)
# ──────────────────────────────────────────────
def search_kipris(keyword: str, ipc_code: str = "", num_rows: int = 20) -> list[dict]:
    if USE_MOCK:
        patents = []
        search_dirs = [ipc_code] if ipc_code else IPC_CODES
        for ipc_dir in search_dirs:
            dir_path = os.path.join(TXT_BASE_DIR, ipc_dir)
            if not os.path.isdir(dir_path):
                print(f"  [경고] 폴더 없음: {dir_path}")
                continue
            for txt_file in glob.glob(os.path.join(dir_path, "*.txt")):
                patent = extract_claim_from_txt(txt_file, ipc=ipc_dir)
                if patent:
                    patents.append(patent)
        print(f"  [{ipc_code or '전체'}] 로컬 txt {len(patents)}건 로드됨")
        return patents

    params = {
        "ServiceKey": KIPRIS_API_KEY,
        "searchWord": keyword,
        "ipcCode":    ipc_code,
        "numOfRows":  num_rows,
        "pageNo":     1,
        "sortSpec":   "AD",
        "descSort":   "true",
    }
    try:
        res   = requests.get(KIPRIS_BASE_URL, params=params, timeout=10)
        res.raise_for_status()
        data  = res.json()
        items = (
            data.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("PatentUtilityInfo", [])
        )
        if isinstance(items, dict):
            items = [items]
        return [
            {
                "app_num":  item.get("applicationNumber", ""),
                "title":    item.get("inventionTitle", ""),
                "abstract": item.get("astrtCont", ""),
                "claim":    item.get("claim", ""),
                "ipc":      item.get("ipcCode", ""),
            }
            for item in items
        ]
    except Exception as e:
        print(f"[KIPRIS 오류] ipc={ipc_code} {e}")
        return []


def search_all_ipc(keyword: str, ipc_codes: list[str] = IPC_CODES) -> list[dict]:
    all_patents = []
    for ipc in ipc_codes:
        results = search_kipris(keyword, ipc_code=ipc)
        all_patents += results

    seen, unique = set(), []
    for p in all_patents:
        if p["app_num"] not in seen:
            seen.add(p["app_num"])
            unique.append(p)

    print(f"[IPC 전체 검색] 총 {len(unique)}건 (중복 제거 후)")
    return unique


# ──────────────────────────────────────────────
# 3. 키워드 필터링
# ──────────────────────────────────────────────
def filter_by_keywords(patents: list[dict], keywords: list[str]) -> list[dict]:
    filtered = []
    for patent in patents:
        full_text = f"{patent['title']} {patent['abstract']} {patent['claim']}"
        if any(kw in full_text for kw in keywords):
            filtered.append(patent)

    if not filtered:
        print(f"[필터링] 키워드 매칭 없음 → 전체 {len(patents)}건으로 진행")
        return patents

    print(f"[필터링] {len(patents)}건 → {len(filtered)}건 (키워드: {keywords})")
    return filtered


# ──────────────────────────────────────────────
# 4. 도면 분석 결과 로드
# ──────────────────────────────────────────────
def load_drawing_text(app_num: str) -> str:
    drawing_file = os.path.join(DRAWING_DIR, f"{app_num}_drawings.json")
    if not os.path.exists(drawing_file):
        return ""
    try:
        with open(drawing_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        keywords = " ".join([d["analysis"] for d in data.get("drawings", [])])
        return keywords[:1000]  # 너무 길면 임베딩 비용 증가하므로 제한
    except Exception as e:
        print(f"[도면 로드 오류] {app_num}: {e}")
        return ""


# ──────────────────────────────────────────────
# 5. 임베딩 & 유사도 비교 (도면 포함)
# ──────────────────────────────────────────────
def get_embedding(text: str) -> list[float]:
    text = text.strip().replace("\n", " ")[:3000]
    res  = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
    )
    return res.data[0].embedding


def compare_claims(my_claim: str, patents: list[dict]) -> list[dict]:
    my_vec  = np.array(get_embedding(my_claim)).reshape(1, -1)
    results = []
    drawing_count = 0

    for patent in patents:
        compare_text = patent["claim"] if patent["claim"] else patent["abstract"]
        if not compare_text:
            continue

        # ✅ 도면 분석 결과 합치기
        drawing_text = load_drawing_text(patent["app_num"])
        if drawing_text:
            compare_text = f"{compare_text} {drawing_text}"
            drawing_count += 1

        patent_vec = np.array(get_embedding(compare_text)).reshape(1, -1)
        score      = cosine_similarity(my_vec, patent_vec)[0][0]
        results.append({
            **patent,
            "similarity":    round(float(score), 4),
            "has_drawing":   bool(drawing_text),
        })

    print(f"  (도면 데이터 활용: {drawing_count}건)")
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results


# ──────────────────────────────────────────────
# 6. LLM 차별성 분석
# ──────────────────────────────────────────────
def analyze_differentiation(my_claim: str, similar_patent: dict) -> str:
    prompt = f"""
다음 두 특허 청구항을 비교하여 분석해줘.

[내 청구항]
{my_claim}

[선행특허 청구항] (출원번호: {similar_patent['app_num']}, 제목: {similar_patent['title']})
{similar_patent['claim'][:800] or similar_patent['abstract']}

아래 형식으로 답변해줘:
1. 겹치는 구성요소: (어떤 부분이 유사한지)
2. 차별성 있는 부분: (내 청구항만의 독자적인 부분)
3. 청구항 개선 제안: (신규성 강화를 위해 수정할 방향)
"""
    res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return res.choices[0].message.content


# ──────────────────────────────────────────────
# 7. DB 저장
# ──────────────────────────────────────────────
def save_to_db(
    user_id:         str,
    consult_seq:     int,
    top_results:     list[dict],
    differentiation: str,
    is_novel:        bool,
) -> None:
    top_sim = top_results[0]["similarity"] if top_results else 0
    supabase.table("consulting").upsert(
        {
            "user_id":          user_id,
            "consultation_idx": consult_seq,
            "summary_problem":  f"유사도 {top_sim:.3f} — {'유사 특허 발견' if not is_novel else '신규성 확보'}",
            "summary_solution": differentiation,
        }
    ).execute()
    print(f"[DB 저장 완료] user_id={user_id}, consultation_idx={consult_seq}, 신규성={is_novel}")


# ──────────────────────────────────────────────
# 8. 메인 파이프라인
# ──────────────────────────────────────────────
def run_prior_art_search(
    user_id:     str,
    consult_seq: int,
    my_claim:    str,
    keywords:    list[str],
    ipc_codes:   list[str] = IPC_CODES,
) -> dict:
    print("\n=== 선행기술조사 시작 ===")
    print(f"키워드: {keywords}")
    print(f"IPC 코드: {ipc_codes}")

    search_query = " ".join(keywords)
    patents      = search_all_ipc(search_query, ipc_codes=ipc_codes)

    if not patents:
        print("[결과 없음] 검색 결과가 없습니다.")
        return {"is_novel": True, "results": [], "differentiation": ""}

    filtered = filter_by_keywords(patents, keywords)

    print(f"\n[임베딩 비교] {len(filtered)}건 비교 중...")
    results = compare_claims(my_claim, filtered)

    print("\n[유사도 상위 결과]")
    for i, r in enumerate(results[:5]):
        drawing_mark = "🖼" if r.get("has_drawing") else "  "
        print(f"  {i+1}. [{r['similarity']:.3f}] {drawing_mark} [{r['ipc']}] {r['title'][:35]}...")

    top      = results[0]
    is_novel = top["similarity"] < SIMILARITY_THRESHOLD

    if not is_novel:
        print(f"\n[유사 특허 발견] 유사도 {top['similarity']:.3f} → 차별성 분석 중...")
        differentiation = analyze_differentiation(my_claim, top)
        print(f"\n[차별성 분석 결과]\n{differentiation}")
    else:
        differentiation = "유사 선행특허 없음 — 신규성 확보 가능"
        print(f"\n[신규성 확보] 최고 유사도 {top['similarity']:.3f}")

    save_to_db(user_id, consult_seq, results, differentiation, is_novel)

    return {
        "is_novel":        is_novel,
        "top_similarity":  top["similarity"],
        "top_patent":      top,
        "all_results":     results,
        "differentiation": differentiation,
    }


# ──────────────────────────────────────────────
# 실행 예시
# ──────────────────────────────────────────────
if __name__ == "__main__":
    my_claim = """
    사용자로부터 상담 요청을 수신하는 입력부;
    대규모 언어 모델(LLM)을 이용하여 상담 내용을 분석하고 응답을 생성하는 처리부;
    생성된 응답을 사용자에게 전달하고 피드백을 수집하는 출력부;
    를 포함하는 AI 기반 특허 상담 시스템.
    """

    keywords = ["사용자 입력", "LLM", "피드백", "상담", "신경망", "AI"]

    result = run_prior_art_search(
        user_id="user_001",
        consult_seq=2,
        my_claim=my_claim,
        keywords=keywords,
        ipc_codes=["G06N", "G06F", "G06V", "G06Q"],
    )