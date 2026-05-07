"""
선행기술조사 — 방법 4 구현
흐름: KIPRIS 검색 → 키워드 필터링 → 전체 청구항 임베딩 비교 → 유사도 판단 → DB 저장
IPC 코드: G06N(AI모델), G06F(데이터처리), G06V(이미지처리), G06Q(AI서비스) 전체 검색
"""

import os
import json
import requests
import numpy as np
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from supabase import create_client

load_dotenv()

# ── 클라이언트 초기화
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase      = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

KIPRIS_API_KEY       = os.getenv("KIPRIS_API_KEY")
KIPRIS_BASE_URL      = "http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/patUtiModInfoSearch"
SIMILARITY_THRESHOLD = 0.75
USE_MOCK             = True   # KIPRIS 키 없을 때 True

# 검색할 IPC 코드 전체
IPC_CODES = ["G06N", "G06F", "G06V", "G06Q"]


# ── Step 1: KIPRIS 검색 (단일 IPC)
def search_kipris(keyword: str, ipc_code: str = "", num_rows: int = 20) -> list[dict]:
    if USE_MOCK:
        return [
            {
                "app_num":  f"10-2023-000{ipc_code[-1]}",
                "title":    f"AI 기반 특허 상담 시스템 ({ipc_code})",
                "abstract": "대규모 언어 모델을 이용한 특허 상담 및 분석 서비스",
                "claim":    "사용자 입력을 수신하는 인터페이스; LLM을 이용해 분석하는 처리부; 결과를 출력하는 피드백부;를 포함하는 AI 상담 시스템.",
                "ipc":      ipc_code,
            },
            {
                "app_num":  f"10-2022-000{ipc_code[-1]}",
                "title":    f"자연어 처리 기반 상담 시스템 ({ipc_code})",
                "abstract": "NLP 모델을 활용한 문서 분석 및 상담 자동화",
                "claim":    "자연어 질의를 입력받는 수신부; NLP 처리부; 상담 결과를 제공하는 출력부;를 포함하는 상담 시스템.",
                "ipc":      ipc_code,
            },
        ]

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
        res = requests.get(KIPRIS_BASE_URL, params=params, timeout=10)
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


# ── Step 1-2: IPC 4개 전체 검색 후 합치기
def search_all_ipc(keyword: str, ipc_codes: list[str] = IPC_CODES) -> list[dict]:
    all_patents = []
    for ipc in ipc_codes:
        results = search_kipris(keyword, ipc_code=ipc)
        all_patents += results
        print(f"  [{ipc}] {len(results)}건 검색됨")

    # 출원번호 기준 중복 제거
    seen = set()
    unique = []
    for p in all_patents:
        if p["app_num"] not in seen:
            seen.add(p["app_num"])
            unique.append(p)

    print(f"[IPC 전체 검색] 총 {len(unique)}건 (중복 제거 후)")
    return unique


# ── Step 2: 키워드 필터링
def filter_by_keywords(patents: list[dict], keywords: list[str]) -> list[dict]:
    filtered = []
    for patent in patents:
        full_text = f"{patent['title']} {patent['abstract']} {patent['claim']}"
        if any(kw in full_text for kw in keywords):
            filtered.append(patent)
    print(f"[필터링] {len(patents)}건 → {len(filtered)}건 (키워드: {keywords})")
    return filtered


# ── Step 3: 임베딩
def get_embedding(text: str) -> list[float]:
    text = text.strip().replace("\n", " ")
    res  = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small",
    )
    return res.data[0].embedding


# ── Step 4: 전체 청구항 임베딩 비교
def compare_claims(my_claim: str, patents: list[dict]) -> list[dict]:
    my_vec  = np.array(get_embedding(my_claim)).reshape(1, -1)
    results = []
    for patent in patents:
        compare_text = patent["claim"] if patent["claim"] else patent["abstract"]
        if not compare_text:
            continue
        patent_vec = np.array(get_embedding(compare_text)).reshape(1, -1)
        score      = cosine_similarity(my_vec, patent_vec)[0][0]
        results.append({**patent, "similarity": round(float(score), 4)})
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results


# ── Step 5: LLM 차별성 분석
def analyze_differentiation(my_claim: str, similar_patent: dict) -> str:
    prompt = f"""
다음 두 특허 청구항을 비교하여 분석해줘.

[내 청구항]
{my_claim}

[선행특허 청구항] (출원번호: {similar_patent['app_num']}, 제목: {similar_patent['title']})
{similar_patent['claim'] or similar_patent['abstract']}

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


# ── Step 6: Supabase 저장
def save_to_db(
    user_id:         str,
    consult_seq:     int,
    top_results:     list[dict],
    differentiation: str,
    is_novel:        bool,
) -> None:
    summary_flow = json.dumps(
        [
            {
                "rank":       i + 1,
                "app_num":    r["app_num"],
                "title":      r["title"],
                "similarity": r["similarity"],
                "ipc":        r["ipc"],
            }
            for i, r in enumerate(top_results[:5])
        ],
        ensure_ascii=False,
    )
    summary_effect = "신규성 확보 가능" if is_novel else "청구항 수정 필요"

    supabase.table("consulting").upsert(
        {
            "user_id":            user_id,
            "consultation_idx":   consult_seq,
            "summary_difference": differentiation,
            "summary_flow":       summary_flow,
            "summary_effect":     summary_effect,
        }
    ).execute()

    print(f"[DB 저장 완료] user_id={user_id}, consultation_idx={consult_seq}, 신규성={is_novel}")


# ── 메인 파이프라인
def run_prior_art_search(
    user_id:     str,
    consult_seq: int,
    my_claim:    str,
    keywords:    list[str],
    ipc_codes:   list[str] = IPC_CODES,   # G06N, G06F, G06V, G06Q 전체
) -> dict:
    print("\n=== 선행기술조사 시작 ===")
    print(f"키워드: {keywords}")
    print(f"IPC 코드: {ipc_codes}")

    # 1. IPC 4개 전체 검색
    search_query = " ".join(keywords)
    patents      = search_all_ipc(search_query, ipc_codes=ipc_codes)

    if not patents:
        print("[결과 없음] KIPRIS 검색 결과가 없습니다.")
        return {"is_novel": True, "results": [], "differentiation": ""}

    # 2. 키워드 필터링
    filtered = filter_by_keywords(patents, keywords)

    if not filtered:
        print("[필터 후 결과 없음] 신규성 확보 가능")
        save_to_db(user_id, consult_seq, [], "관련 선행특허 없음", is_novel=True)
        return {"is_novel": True, "results": [], "differentiation": "관련 선행특허 없음"}

    # 3 & 4. 전체 청구항 임베딩 비교
    print(f"\n[임베딩 비교] {len(filtered)}건 비교 중...")
    results = compare_claims(my_claim, filtered)

    print("\n[유사도 상위 결과]")
    for i, r in enumerate(results[:5]):
        print(f"  {i+1}. [{r['similarity']:.3f}] [{r['ipc']}] {r['title'][:35]}...")

    # 5. 신규성 판단
    top      = results[0]
    is_novel = top["similarity"] < SIMILARITY_THRESHOLD

    if not is_novel:
        print(f"\n[유사 특허 발견] 유사도 {top['similarity']:.3f} → 차별성 분석 중...")
        differentiation = analyze_differentiation(my_claim, top)
        print(f"\n[차별성 분석 결과]\n{differentiation}")
    else:
        differentiation = "유사 선행특허 없음 — 신규성 확보 가능"
        print(f"\n[신규성 확보] 최고 유사도 {top['similarity']:.3f}")

    # 6. DB 저장
    save_to_db(user_id, consult_seq, results, differentiation, is_novel)

    return {
        "is_novel":        is_novel,
        "top_similarity":  top["similarity"],
        "top_patent":      top,
        "all_results":     results,
        "differentiation": differentiation,
    }


# ── 실행
if __name__ == "__main__":
    my_claim = """
    사용자로부터 상담 요청을 수신하는 입력부;
    대규모 언어 모델(LLM)을 이용하여 상담 내용을 분석하고 응답을 생성하는 처리부;
    생성된 응답을 사용자에게 전달하고 피드백을 수집하는 출력부;
    를 포함하는 AI 기반 특허 상담 시스템.
    """

    keywords = ["사용자 입력", "LLM", "피드백", "상담"]

    result = run_prior_art_search(
        user_id="user_001",
        consult_seq=1,
        my_claim=my_claim,
        keywords=keywords,
        ipc_codes=["G06N", "G06F", "G06V", "G06Q"],  # 4개 전체 검색
    )