"""
선행기술조사 에이전트
- S3 XML → RDS pgvector 기반 임베딩 유사도 검색
- PatentState.claims_data → 쿼리 추출 → pgvector Top-N 검색 → 근거문장 + 리스크 분석
"""

import time
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import contextvars
import numpy as np
from openai import OpenAI
from langsmith import traceable   #langsmith tracing 데코레이터
from langsmith.wrappers import wrap_openai  # 💡 추가: OpenAI 클라이언트를 LangSmith용으로 감싸주는 래퍼
import urllib.parse  # URL 인코딩용 (추가)
import requests      # 외부 API HTTP 요청용 (추가)
import xml.etree.ElementTree as ET  # XML 파싱용 (추가)
from dotenv import load_dotenv
from sqlalchemy import Text
from agents.core.state import (
    ClaimResult,
    PatentState,
    PriorArtCandidate,
    PriorArtResult,
)
from agents.prior_art_agent.patent_db import PatentCorpus, SessionLocal

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

client = wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

EMBED_MODEL   = "text-embedding-3-small"
ANALYZE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANALYZE_MAX_WORKERS = int(os.getenv("PRIOR_ART_ANALYZE_MAX_WORKERS", "5"))


# ─────────────────────────────────────────────────────────────
# 1. 임베딩 유틸
# ─────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> np.ndarray:
    """OpenAI 임베딩 API 배치 호출 (load_corpus.py에서도 재사용)"""
    batch_size = 100
    all_vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vecs = [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]
        all_vecs.extend(vecs)
    return np.array(all_vecs, dtype=np.float32)


# ─────────────────────────────────────────────────────────────
# 2. ClaimResult → 청구항 1 검색 쿼리 텍스트 추출
# ─────────────────────────────────────────────────────────────

def _build_claim1_query_text(claims_data: ClaimResult) -> str:
    claim1 = next(
        (claim for claim in claims_data.claims if claim.claim_no == 1),
        None,
    )
    
    if claim1 is None or not claim1.content:
        return ""
    
    return claim1.content.strip()
    

# ─────────────────────────────────────────────────────────────
# 3. pgvector 기반 Top-N 검색
# ─────────────────────────────────────────────────────────────

@traceable(run_type="tool", name="Local_DB_Search")  # 💡 추가: 로컬 DB 검색을 Tool로 명시적 트레이싱
def search_similar_patents(
    query_text: str,
    top_n: int = 5,
    ipc_prefix: str = None,
) -> list[dict]:
    embed_started_at = time.perf_counter()
    query_vec = embed_texts([query_text])[0].tolist()
    print(f"[선행기술조사] 쿼리 임베딩 소요: {time.perf_counter() - embed_started_at:.2f}초")

    db = SessionLocal()
    try:
        search_started_at = time.perf_counter()
        # 거리값을 결과와 함께 가져오기 위해 label로 추가
        # 이렇게 해야 각 결과별 similarity_score를 정확히 계산 가능
        distance_col = PatentCorpus.embedding.cosine_distance(query_vec).label("distance")

        q = db.query(PatentCorpus, distance_col)

        # IPC 필터: 기술 분야가 명확하면 관련 없는 특허 미리 제거
        if ipc_prefix:
            q = q.filter(
                PatentCorpus.ipc_codes.cast(Text).like(f"%{ipc_prefix}%")
            )

        rows = q.order_by(distance_col).limit(top_n).all()
        print(f"[선행기술조사] DB 유사도 검색 소요: {time.perf_counter() - search_started_at:.2f}초")

        return [
            {
                "patent_id":  row.PatentCorpus.id,
                "register_number": row.PatentCorpus.register_number,
                "title":          row.PatentCorpus.title,
                "applicant":      row.PatentCorpus.applicant,
                "abstract":       row.PatentCorpus.abstract,
                "claims":         row.PatentCorpus.claim1,
                "ipc_codes":      row.PatentCorpus.ipc_codes,
                "examiner_cited": row.PatentCorpus.examiner_cited,
                "pdf_s3_url":     row.PatentCorpus.pdf_s3_url,
                "similarity_score": round(1 - float(row.distance) / 2, 4),
            }
            for row in rows
        ]
    finally:
        db.close()

# ─────────────────────────────────────────────────────────────
# 3-1. (신규) 외부 API 기반 검색 함수 (KIPRIS 등)
# ─────────────────────────────────────────────────────────────
def _generate_kipris_query(claim_text: str) -> str:
    """청구항 1항 텍스트를 KIPRIS API용 검색식으로 변환"""
    prompt = f"""당신은 특허 선행기술조사 전문가입니다.
아래 특허 청구항에서 기술적 핵심 구성요소 3~4개를 추출하여 KIPRIS 검색식을 작성하세요.

[청구항]
{claim_text}

[지침]
1. 불필요한 단어(상기, 포함하는, 특징으로 하는, 시스템, 방법 등)는 완전히 제거하세요.
2. 각 구성요소의 유의어/동의어를 '+'(OR)로 묶고, 구성요소 간에는 '*'(AND)로 묶으세요.
3. 괄호를 사용하여 연산자 우선순위를 명확히 하세요.
4. 출력은 오직 검색식 문자열만 반환하세요. (따옴표나 설명 금지)

예시 출력: (센서+감지기)*(무선+블루투스)*(네트워크+통신)"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini", # 전처리는 빠르고 저렴한 모델 사용
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()


def _fetch_kipris_details(app_number: str, service_key: str) -> dict:
    """
    개별 출원번호에 대해 서지상세정보(청구항)와 공개전문PDF 링크를 병렬로 가져옵니다.
    """
    details = {"claim1": "", "pdf_url": ""}
    
    # 1. 서지상세조회 (청구항 추출)
    detail_url = f"http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getBibliographyDetailInfoSearch?applicationNumber={app_number}&ServiceKey={service_key}"
    try:
        res_detail = requests.get(detail_url, timeout=5)
        root_detail = ET.fromstring(res_detail.text)
        
        # <claimInfoArray>에서 청구항 1항 찾기
        for claim_elem in root_detail.findall('.//claimInfo/claim'):
            claim_text = claim_elem.text if claim_elem.text else ""
            # "1."으로 시작하거나 첫 번째 청구항인 경우 (안전하게 1항 추출)
            if claim_text.strip().startswith("1."):
                details["claim1"] = claim_text.strip()
                break
        
        # 만약 "1."으로 시작하는게 없다면 첫 번째 청구항을 기본값으로 사용
        if not details["claim1"]:
            first_claim = root_detail.findtext('.//claimInfo/claim', default="")
            details["claim1"] = first_claim.strip()
            
    except Exception as e:
        print(f"[{app_number}] 서지상세정보 호출 실패: {e}")

    # 2. 공개전문 PDF 조회
    pdf_url = f"http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getPubFullTextInfoSearch?applicationNumber={app_number}&ServiceKey={service_key}"
    try:
        res_pdf = requests.get(pdf_url, timeout=5)
        root_pdf = ET.fromstring(res_pdf.text)
        pdf_path = root_pdf.findtext('.//item/path', default="")
        details["pdf_url"] = pdf_path.strip()
    except Exception as e:
        print(f"[{app_number}] PDF 정보 호출 실패: {e}")

    return details

@traceable(run_type="tool", name="KIPRIS_API_Search")  # 💡 추가: 외부 API 검색을 Tool로 명시적 트레이싱
def search_external_api(query_text: str, top_n: int = 5) -> list[dict]:
    """KIPRIS API를 호출하여 선행기술문헌 목록과 상세 데이터를 종합합니다."""
    service_key = os.getenv("KIPRIS_API_KEY")
    if not service_key:
        print("[에러] 환경변수에 KIPRIS_API_KEY가 없습니다.")
        return []

    # 1. 청구항 -> KIPRIS 검색식 변환
    kipris_query = _generate_kipris_query(query_text)
    print(f"[외부 API] 생성된 KIPRIS 검색식: {kipris_query}")
    
    # 2. 고급 검색 (목록 조회)
    encoded_query = urllib.parse.quote(kipris_query)
    search_url = f"http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch?word={encoded_query}&ServiceKey={service_key}&numOfRows={top_n}"
    
    try:
        response = requests.get(search_url, timeout=10)
        root = ET.fromstring(response.text)
        items = root.findall('.//item')
    except Exception as e:
        print(f"[외부 API 검색 에러] {e}")
        return []

    if not items:
        return []

    # 기본 특허 리스트 파싱
    base_patents = []
    for item in items:
        app_number = item.findtext('applicationNumber', default="").strip()
        if not app_number:
            continue
            
        base_patents.append({
            "patent_id": app_number, # 출원번호를 ID로 사용
            "register_number": item.findtext('registerNumber', default="").strip(),
            "title": item.findtext('inventionTitle', default="").strip(),
            "applicant": item.findtext('applicantName', default="").strip(),
            "abstract": item.findtext('astrtCont', default="").strip(),
            "ipc_codes": item.findtext('ipcNumber', default="").strip(),
            "similarity_score": 0.0, # KIPRIS는 점수를 주지 않으므로 임시값
        })

    print(f"[외부 API] {len(base_patents)}건의 목록 확보. 상세정보 및 PDF 수집 시작...")

    # 3. 상세 정보(청구항 1항, PDF 링크) 병렬 수집 (속도 최적화)
    # ThreadPoolExecutor를 사용해 상세 API 여러 번 호출에 따른 병목을 제거합니다.
    with ThreadPoolExecutor(max_workers=len(base_patents)) as executor:
        future_to_patent = {
            executor.submit(_fetch_kipris_details, p["patent_id"], service_key): p
            for p in base_patents
        }
        
        for future in as_completed(future_to_patent):
            patent = future_to_patent[future]
            try:
                details = future.result()
                # 기존 딕셔너리에 상세 데이터 결합
                patent["claims"] = details["claim1"]
                patent["pdf_s3_url"] = details["pdf_url"]
                patent["examiner_cited"] = False # 기본값
            except Exception as e:
                patent["claims"] = ""
                patent["pdf_s3_url"] = ""
                patent["examiner_cited"] = False

    return base_patents

# ─────────────────────────────────────────────────────────────
# 4. LLM 기반 근거 문장 + 리스크 분석
# ─────────────────────────────────────────────────────────────
@traceable(run_type="llm")
def _analyze_patent(claims_data: ClaimResult, patent: dict) -> dict:
    claim1_text = _build_claim1_query_text(claims_data)

    patent_body = "\n".join(filter(None, [
        f"제목: {patent.get('title', '')}",
        f"출원번호: {patent.get('register_number', '')}",
        f"선행특허 청구항 1: {patent.get('claims', '')}",
        f"요약: {patent.get('abstract', '')}",
    ]))

    prompt = f"""당신은 대한민국 특허법 전문 변리사입니다.
아래 [본원 청구항]과 [선행특허]를 비교하여 신규성·진보성 거절 리스크를 분석하세요.

─── 본원 청구항 1 ───
{claim1_text}

─── 선행특허 ───
{patent_body[:2500]}

─── 지침 ───
1. 본원 청구항 1과 선행특허 청구항 1에서 실제로 겹치는 구성요소, 동작, 효과를 근거문장으로 추출하세요.
2. 청구항 문언 기준으로 판단하세요.
3. 추측하지 말고 텍스트에 명시된 내용만 사용하세요.
4. risk_level: high(본원 청구항의 핵심 구성이 대부분 개시됨), medium(일부 핵심 구성이 유사함), low(관련성 낮음)

반드시 아래 JSON만 출력하세요:
{{
  "summary": "선행특허 핵심 요약",
  "overlap_points": ["본원 청구항 1과 겹치는 점"],
  "difference_points": ["본원 청구항 1과 다른 점"],
  "limitations": ["선행기술 또는 종래기술의 한계"],
  "evidence_sentences": [
    {{
      "patent_text": "선행특허의 근거 구절",
      "invention_text": "본원 청구항 1의 대응 내용",
      "overlap_type": "동일|유사|관련"
    }}
  ],
  "risk_level": "high|medium|low",
  "risk_reasons": ["리스크 이유"],
  "recommendation": "본원 청구항 보정 또는 대응 전략"
}}"""

    resp = client.chat.completions.create(
        model=ANALYZE_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_completion_tokens=3000,
    )
    return json.loads(resp.choices[0].message.content)


# ─────────────────────────────────────────────────────────────
# 5. 전체 리스크 요약
# ─────────────────────────────────────────────────────────────

def _summarize_overall_risk(results: list[dict]) -> dict:
    high   = sum(1 for r in results if r.get("risk_level") == "high")
    medium = sum(1 for r in results if r.get("risk_level") == "medium")
    low    = sum(1 for r in results if r.get("risk_level") == "low")

    if high >= 2:
        level = "high"
        summary = f"고위험 선행특허 {high}건 발견 — 청구항 범위 조정 및 회피설계 필요"
    elif high == 1 or medium >= 2:
        level = "medium"
        summary = f"주의 필요 선행특허 {high + medium}건 — 차별점 강조 및 청구항 보완 권장"
    else:
        level = "low"
        summary = "주요 저촉 선행기술 미발견 — 현재 방향으로 출원 진행 가능"

    return {
        "level": level,
        "summary": summary,
        "counts": {"high": high, "medium": medium, "low": low},
    }


def _merge_unique(groups: list[list[str]]) -> list[str]:
    merged = []
    seen = set()
    #같은 문장 중복 X
    for group in groups:
        for item in group:
            if item and item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


# ─────────────────────────────────────────────────────────────
# 6. 메인 에이전트 함수
# ─────────────────────────────────────────────────────────────

@traceable(run_type="chain", name="Prior_Art_Router_Agent")
def run_prior_art_agent(
    state: PatentState,
    top_n: int = 5,
) -> dict:
    total_started_at = time.perf_counter()
    claims_data = state.get("claims_data")
    if claims_data is None or not claims_data.claims:
        return {"prior_art_data": PriorArtResult(candidates=[])}

    query_text = _build_claim1_query_text(claims_data)
    if not query_text:
        return {"prior_art_data": PriorArtResult(candidates=[])}

    print(f"[선행기술조사] 청구항 1 추출 완료:\n  {query_text[:200]}...")

    # ---------------------------------------------------------
    # [Agentic Tool Calling 로직] 판단 및 도구 선택
    # ---------------------------------------------------------
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_similar_patents",
                "description": "인공지능(AI), 머신러닝, 딥러닝, 소프트웨어 아키텍처 등과 관련된 발명일 때 로컬 벡터 DB를 검색합니다. 컴퓨터과학 등, CS 분야도 AI 관련 기술로 간주하여 검색합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "검색할 청구항 텍스트"}
                    },
                    "required": ["query_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_external_api",
                "description": "기계, 화학, 바이오 등 인공지능과 무관한 발명일 때 KIPRIS 등 외부 특허 API를 검색합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_text": {"type": "string", "description": "외부 API 검색을 위한 주요 키워드 또는 문장"}
                    },
                    "required": ["query_text"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "당신은 특허 검색 라우터 에이전트입니다. 입력된 청구항 내용을 분석하여, AI 기술이면 'search_similar_patents'를, 비-AI 기술이면 'search_external_api' 도구를 호출하세요."},
        {"role": "user", "content": query_text}
    ]

    print("[선행기술조사] LLM 에이전트가 적절한 검색 도구를 결정 중입니다...")
    decision_resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = decision_resp.choices[0].message
    top_patents = []
    
    search_source_val = "UNKNOWN" # 💡 소스 추적용 변수 추가

    # LLM이 도구(Tool) 호출을 결정했는지 확인
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        search_total_started_at = time.perf_counter()
        
        if function_name == "search_similar_patents":
            print("[선행기술조사 에이전트] 판단 결과: AI 기술 -> 로컬 pgvector DB 호출")
            search_source_val = "LOCAL_DB" # 💡 추가
            top_patents = search_similar_patents(query_text=function_args.get("query_text", query_text), top_n=top_n)
        elif function_name == "search_external_api":
            print("[선행기술조사 에이전트] 판단 결과: 비-AI 기술 -> 외부 검색 API 호출")
            search_source_val = "EXTERNAL_API" # 💡 추가
            top_patents = search_external_api(query_text=function_args.get("query_text", query_text), top_n=top_n)
            
        print(f"[선행기술조사] 검색 완료 소요시간: {time.perf_counter() - search_total_started_at:.2f}초")
    else:
        # Tool을 호출하지 않은 예외 상황 (Fallback으로 로컬 DB 검색)
        search_source_val = "LOCAL_DB"  # 💡 추가
        print("[선행기술조사 에이전트] 명시적 툴 호출 실패. 기본 로컬 검색으로 폴백합니다.")
        top_patents = search_similar_patents(query_text, top_n=top_n)

    # 검색된 결과가 없으면 종료
    if not top_patents:
        return {"prior_art_data": PriorArtResult(candidates=[])}

    print(f"[선행기술조사] 유사 특허 Top-{len(top_patents)} 선정 완료. 리스크 분석 시작.")

    def _analyze_one(index: int, patent: dict) -> tuple[int, dict, dict]:
        print(f"[선행기술조사] 분석 시작 {index+1}/{len(top_patents)}: {patent.get('title', '')[:50]}")
        analyze_started_at = time.perf_counter()
        try:
            analysis = _analyze_patent(claims_data, patent)
        except Exception as e:
            analysis = {
                "summary": "",
                "overlap_points": [],
                "difference_points": [],
                "limitations": [],
                "evidence_sentences": [],
                "risk_level": "unknown",
                "risk_reasons": [f"분석 실패: {str(e)}"],
                "recommendation": "",
            }
        print(f"[선행기술조사] 분석 {index+1}/{len(top_patents)} 소요: {time.perf_counter() - analyze_started_at:.2f}초")
        return index, patent, analysis

    max_workers = max(1, min(ANALYZE_MAX_WORKERS, len(top_patents)))
    print(f"[선행기술조사] 후보 분석 병렬 실행: workers={max_workers}")

    analysis_items = []
    # 💡 추가 1: 현재 실행 중인 부모(Router Agent)의 트레이싱 컨텍스트를 복사합니다.
    # ctx = contextvars.copy_context()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(contextvars.copy_context().run, _analyze_one, i, patent)
            for i, patent in enumerate(top_patents)
        ]
        for future in as_completed(futures):
            analysis_items.append(future.result())

    analysis_items.sort(key=lambda item: item[0])

    candidates = []
    prior_art_results = []
    for i, patent, analysis in analysis_items:

        overlap_points    = analysis.get("overlap_points", [])
        difference_points = analysis.get("difference_points", [])
        limitations       = analysis.get("limitations", [])
        evidence_sentences = analysis.get("evidence_sentences", [])

        candidates.append(
            PriorArtCandidate(
                patent_id=patent["patent_id"],
                rank=i + 1,
                register_number=patent.get("register_number", ""),
                title=patent.get("title", ""),
                summary=analysis.get("summary", ""),
                score=patent.get("similarity_score", 0.0),
                overlap_points=overlap_points,
                difference_points=difference_points,
                limitations=limitations,
                evidence=[
                    evidence.get("patent_text", "")
                    for evidence in evidence_sentences
                    if isinstance(evidence, dict) and evidence.get("patent_text")
                ],
                risk_level=analysis.get("risk_level", "unknown"),
                risk_reasons=analysis.get("risk_reasons", []),
                recommendation=analysis.get("recommendation", ""),
                pdf_s3_url=patent.get("pdf_s3_url"),
            )
        )

        prior_art_results.append({
            "rank":             i + 1,
            "register_number":    patent.get("register_number", ""),
            "title":            patent.get("title", ""),
            "applicant":        patent.get("applicant", ""),
            "similarity_score": patent.get("similarity_score", 0.0),
            "differentiating_points": difference_points,
            **analysis,
        })

    overall_risk = _summarize_overall_risk(prior_art_results)
    print(f"\n[선행기술조사] 완료 — 전체 리스크: {overall_risk['level'].upper()}")
    print(f"[선행기술조사] 전체 실행 소요: {time.perf_counter() - total_started_at:.2f}초")

    overlap_points = _merge_unique([c.overlap_points for c in candidates])
    difference_points = _merge_unique([c.difference_points for c in candidates])
    limitations = _merge_unique([c.limitations for c in candidates])
    
    analysis_summary = " ".join(filter(None, [
        f"종래기술은 {overlap_points[0]} 측면에서 관련성이 있습니다." if overlap_points else "",
        f"다만 {limitations[0]} 한계가 있습니다." if limitations else "",
        f"본 발명은 {difference_points[0]} 점에서 차별화됩니다." if difference_points else "",
    ])) or overall_risk["summary"]

    return {
        "prior_art_data": PriorArtResult(
            candidates=candidates,
            overall_risk=overall_risk,
            analysis_summary=analysis_summary,
            search_source=search_source_val # 💡 추가
        )
    }


# ─────────────────────────────────────────────────────────────
# CLI 실행 (테스트용)
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    sample_claims = {
        "claims": [
            {
                "claim_no": 1,
                "is_dependent": False,
                "cited_claim_no": [],
                "category": "시스템",
                "content": (
                    "복수의 사용자 댓글을 입력받는 입력부; 상기 복수의 사용자 댓글 각각을 "
                    "의미 벡터로 변환하는 댓글 임베딩부; 상기 의미 벡터 간의 유사도를 산출하여 "
                    "유사 댓글 그룹을 생성하는 군집화부; 및 상기 유사 댓글 그룹별로 대표 댓글을 "
                    "생성하여 출력하는 대표 댓글 생성부를 포함하는 의미 기반 댓글 통합 시스템."
                ),
            },
            {
                "claim_no": 2,
                "is_dependent": True,
                "cited_claim_no": [1],
                "category": "시스템",
                "content": (
                    "제1항에 있어서, 상기 대표 댓글 생성부는 유사 댓글 그룹에 포함된 댓글들의 "
                    "공통 의미를 요약하여 하나의 대표 문장을 생성하는 의미 기반 댓글 통합 시스템."
                ),
            },
        ]
    }

    payload_path = sys.argv[1] if len(sys.argv) > 1 else None
    if payload_path and os.path.exists(payload_path):
        with open(payload_path, encoding="utf-8") as f:
            sample_claims = json.load(f)

    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    sample_state: PatentState = {
        "mock_input_data": {},
        "summary_data": None,
        "claims_data": ClaimResult.model_validate(sample_claims),
        "prior_art_data": None,
        "examiner_data": None,
    }

    result = run_prior_art_agent(sample_state, top_n=top_n)
    print("\n" + "=" * 60)
    print(result["prior_art_data"].model_dump_json(indent=2))
