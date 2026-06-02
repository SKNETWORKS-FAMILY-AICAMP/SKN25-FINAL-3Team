import os
import argparse
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from dotenv import load_dotenv

from agents.priorart.xml_parser import parse_kipris_xml, build_embed_text
from agents.priorart.patent_db import PatentCorpus, SessionLocal, init_db
from agents.priorart.prior_art_agent import embed_texts

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

S3_BUCKET = os.getenv("S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX", "kipris/raw/bibliography_xml/")

def _download_one(s3, bucket: str, key: str) -> tuple[str, bytes]:
    return key, s3.get_object(Bucket=bucket, Key=key)["Body"].read()

def stream_xml_from_s3(bucket: str, prefix: str):
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    # 전체 키 목록 먼저 수집
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".xml"):
                keys.append(obj["Key"])

    print(f"[적재] S3 XML 파일 {len(keys)}건 발견")

    # 10개씩 동시 다운로드
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_download_one, s3, bucket, k): k for k in keys}
        for future in as_completed(futures):
            try:
                yield future.result()
            except Exception as e:
                print(f"[적재] 다운로드 실패 {futures[future]}: {e}")

def load_to_db(bucket: str = None, prefix: str = None, reset: bool = False):
    init_db()

    bucket = bucket or S3_BUCKET
    prefix = prefix or S3_PREFIX

    if reset:
        db = SessionLocal()
        deleted = db.query(PatentCorpus).delete()
        db.commit()
        db.close()
        print(f"[적재] 기존 데이터 {deleted}건 삭제")
    db = SessionLocal()
    existing = {r.application_number for r in 
        db.query(PatentCorpus.application_number).all()}
    db.close()

    batch, total_saved = [], 0
    BATCH_SIZE = 50 

    for s3_key, xml_bytes in stream_xml_from_s3(bucket, prefix):
        try:
            patent = parse_kipris_xml(xml_bytes)
        except Exception as e:
            print(f"[적재] 파싱 실패: {s3_key}: {e}")
            continue
        
        app_num = patent["application_number"]

        # 출원번호가 없거나 이미 DB에 있으면 스킵
        if not app_num or app_num in existing:
            continue

        patent["embed_text"] = build_embed_text(patent)
        batch.append(patent)

        if len(batch) >= BATCH_SIZE:
            _save_batch(batch)
            total_saved += len(batch)
            print(f"[적재] {total_saved}건 저장 완료")
            batch = []

    # 마지막 남은 배치 처리
    if batch:
        _save_batch(batch)
        total_saved += len(batch)

    print(f"\n[적재] 완료 — 총 {total_saved}건 저장")

def _save_batch(batch: list[dict]):
    # 임베딩은 배치로 한 번에 호출하는 이유:
    # OpenAI API는 건당 호출보다 배치가 훨씬 빠르고 비용도 절약
    texts = [p["embed_text"] for p in batch]
    vectors = embed_texts(texts)  # prior_art_agent의 기존 함수 재활용

    db = SessionLocal()
    try:
        for patent, vec in zip(batch, vectors):
            db.add(PatentCorpus(
                application_number = patent["application_number"],
                register_number    = patent["register_number"],
                title              = patent["title"],
                abstract           = patent["abstract"],
                claim1             = patent["claim1"],
                ipc_codes          = patent["ipc_codes"],
                examiner_cited     = patent["examiner_cited"],
                applicant          = patent["applicant"],
                embedding          = vec.tolist(),
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[적재] DB 저장 실패: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", default=None)
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    load_to_db(args.bucket, args.prefix, args.reset)