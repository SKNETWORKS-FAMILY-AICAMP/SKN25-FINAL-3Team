"""
특허 TXT 파일을 파싱·임베딩하여 Supabase DB에 적재하는 스크립트.

사용법:
    python load_corpus.py               # patents_txt/ 전체 적재 (중복 제외)
    python load_corpus.py --reset       # 기존 데이터 삭제 후 전체 재적재
    python load_corpus.py --dir /path   # 특정 디렉토리 지정
"""

import argparse
from pathlib import Path

# 패키지(agents.consultation)로 import될 때와 스크립트로 직접 실행될 때를 모두 지원
try:
    from agents.consultation.prior_art_agent import _parse_patent_txt, _embed_texts, PATENTS_DIR
    from agents.consultation.patent_db import PatentCorpus, SessionLocal, init_db
except ImportError:
    from prior_art_agent import _parse_patent_txt, _embed_texts, PATENTS_DIR  # type: ignore[no-redef]
    from patent_db import PatentCorpus, SessionLocal, init_db  # type: ignore[no-redef]


def _get_ipc_class(file_path: str) -> str:
    """경로에서 IPC 분류 추출. extracted_texts/G06F/xxx.txt → 'G06F'"""
    for part in Path(file_path).parts:
        if len(part) == 4 and part.startswith("G"):
            return part
    return ""


def _load_txt_files(patents_dir: Path) -> list[dict]:
    files = list(patents_dir.glob("*.txt")) + list(patents_dir.glob("**/*.txt"))
    files = list(set(files))

    corpus = []
    for fp in files:
        try:
            patent = _parse_patent_txt(str(fp))
            # 폴더 포함 상대 경로를 고유 키로 사용 (같은 파일명이 다른 폴더에 있을 때 대비)
            patent["file_path_key"] = str(fp.relative_to(patents_dir))
            corpus.append(patent)
        except Exception as e:
            print(f"[적재] {fp.name} 파싱 실패: {e}")

    print(f"[적재] TXT 파일 {len(corpus)}건 파싱 완료")
    return corpus


def _build_search_text(patent: dict) -> str:
    parts = []
    if patent["title"]:    parts.append(patent["title"])
    if patent["abstract"]: parts.append(patent["abstract"][:800])
    if patent["claims"]:   parts.append(patent["claims"][:800])
    if not parts:          parts.append(patent["raw_text"][:1500])
    return " ".join(parts)


def load_to_db(patents_dir: str = None, reset: bool = False):
    init_db()

    target_dir = Path(patents_dir) if patents_dir else PATENTS_DIR

    if reset:
        db = SessionLocal()
        deleted = db.query(PatentCorpus).delete()
        db.commit()
        db.close()
        print(f"[적재] 기존 데이터 {deleted}건 삭제 완료")

    corpus = _load_txt_files(target_dir)
    if not corpus:
        print("[적재] 로드할 파일이 없습니다.")
        return

    # 이미 DB에 있는 경로 확인 (중복 방지)
    db = SessionLocal()
    existing = {r.file_path_key for r in db.query(PatentCorpus.file_path_key).all()}
    db.close()

    new_patents = [p for p in corpus if p["file_path_key"] not in existing]
    print(f"[적재] 전체 {len(corpus)}건 중 신규 {len(new_patents)}건 적재 예정")

    if not new_patents:
        print("[적재] 추가할 새 파일이 없습니다.")
        return

    # 50건 단위로 임베딩 생성 + DB 삽입을 함께 처리
    # → 중간에 오류 나도 이전 배치는 이미 저장됨
    BATCH = 50
    total_saved = 0

    for batch_start in range(0, len(new_patents), BATCH):
        batch = new_patents[batch_start : batch_start + BATCH]
        batch_num = batch_start // BATCH + 1
        total_batches = (len(new_patents) + BATCH - 1) // BATCH
        print(f"[적재] 배치 {batch_num}/{total_batches} — 임베딩 생성 중 ({len(batch)}건)...")

        try:
            search_texts = [_build_search_text(p) for p in batch]
            vectors = _embed_texts(search_texts)
        except Exception as e:
            print(f"[적재] 배치 {batch_num} 임베딩 실패: {e}")
            continue

        db = SessionLocal()
        try:
            for patent, vec in zip(batch, vectors):
                db.add(PatentCorpus(
                    patent_number = patent.get("patent_number", ""),
                    title         = patent.get("title", ""),
                    applicant     = patent.get("applicant", ""),
                    abstract      = patent.get("abstract", ""),
                    claims        = patent.get("claims", ""),
                    description   = patent.get("description", ""),
                    raw_text      = patent.get("raw_text", "")[:5000],
                    ipc_class     = _get_ipc_class(patent["file_path"]),
                    file_name     = patent["file_name"],
                    file_path_key = patent["file_path_key"],
                    embedding     = vec.tolist(),
                ))
            db.commit()
            total_saved += len(batch)
            print(f"[적재] 배치 {batch_num}/{total_batches} 완료 — 누적 {total_saved}건 저장")
        except Exception as e:
            db.rollback()
            print(f"[적재] 배치 {batch_num} DB 삽입 실패: {e}")
        finally:
            db.close()

    print(f"\n[적재] 완료 — 총 {total_saved}건 DB 저장")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="특허 코퍼스 DB 적재 스크립트")
    parser.add_argument("--dir",   default=None, help="TXT 파일 디렉토리 경로")
    parser.add_argument("--reset", action="store_true", help="기존 데이터 삭제 후 재적재")
    args = parser.parse_args()
    load_to_db(args.dir, args.reset)
