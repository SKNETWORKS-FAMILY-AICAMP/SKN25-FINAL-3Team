import re 
from lxml import etree 

def parse_kipris_xml(xml_bytes: bytes) -> dict:
    root = etree.fromstring(xml_bytes)

    claim1 = ""
    for claim_el in root.findall(".//claimInfo/claim"):
        text = (claim_el.text or "").strip()
        if text and text != "삭제" and not text.startswith("삭제"):
            # "1. 텍스트..." 앞의 번호 제거 → 순수 청구항 내용만 임베딩
            claim1 = re.sub(r"^\d+\.\s*", "", text)
            break
    # IPC 코드 리스트로 저장
    # - String 하나가 아닌 리스트인 이유: 특허 하나에 IPC가 여러 개 붙음
    #   (샘플에서 G06F 30/398, G06F 30/367 등 10개)
    # - 나중에 IPC 기반 필터링 할 때 활용
    ipc_codes = [
        el.text.strip()
        for el in root.findall(".//ipcNumber")
        if el.text and el.text.strip()
    ]

    # 심사관 인용 선행문헌
    # - 임베딩/검색에는 안 쓰지만 저장해두는 이유:
    #   에이전트가 찾은 결과와 심사관이 실제 인용한 문헌을 비교해서
    #   에이전트 정확도 검증할 때 정답 레이블로 활용 가능
    examiner_cited = [
        el.text.strip()
        for el in root.findall(".//documentsNumber")
        if el.text and el.text.strip()
    ]

    return {
        "application_number": (root.findtext(".//applicationNumber") or "").strip(),
        "register_number":    (root.findtext(".//registerNumber") or "").strip(),
        "title":              (root.findtext(".//inventionTitle") or "").strip(),
        "abstract":           (root.findtext(".//astrtCont") or "").strip(),
        "claim1":             claim1,
        "ipc_codes":          ipc_codes,
        "applicant":          (root.findtext(".//applicantInfo/name") or "").strip(),
        "examiner_cited":     examiner_cited,
    }


def build_embed_text(patent: dict) -> str:
    parts = []

    if patent.get("title"):
        parts.append(patent["title"])

    if patent.get("claim1"):
        # claim1을 2번 넣는 이유:
        # 임베딩은 텍스트 빈도에 영향받음 → 2번 반복하면
        # 벡터가 claim1 방향으로 더 강하게 당겨져서 검색 정확도 향상
        parts.extend([patent["claim1"]] * 2)
    elif patent.get("abstract"):
        # claim1 파싱 실패(태그 없거나 전부 삭제)한 특허도
        # 검색 대상에서 빠지면 안 되므로 abstract로 대체
        parts.append(patent["abstract"])

    # 2000자 제한 이유:
    # text-embedding-3-small 토큰 한도(8192) 초과 방지
    # 청구항 1항은 보통 500~1500자 수준이라 여유 있음
    return " ".join(parts)[:2000]