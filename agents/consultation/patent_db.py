import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

_ENV_DIR = Path(__file__).resolve().parent
load_dotenv(_ENV_DIR.parents[1] / ".env")
load_dotenv(_ENV_DIR / ".env", override=True)

Base = declarative_base()

EMBEDDING_DIM = 1536  # text-embedding-3-small


class PatentCorpus(Base):
    __tablename__ = "patent_corpus"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    patent_number = Column(String(50))
    title         = Column(Text)
    applicant     = Column(Text)
    abstract      = Column(Text)
    claims        = Column(Text)
    description   = Column(Text)
    raw_text      = Column(Text)
    ipc_class     = Column(String(20))   # G06F, G06N, G06Q, G06V 등
    file_name     = Column(String(200))
    file_path_key = Column(String(500), unique=True)  # 폴더 포함 상대 경로 (중복 방지)
    embedding     = Column(Vector(EMBEDDING_DIM))     # pgvector — DB 엔진이 직접 ANN 검색


def _build_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user     = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    host     = os.getenv("DB_HOST", "")
    port     = os.getenv("DB_PORT", "5432")
    name     = os.getenv("DB_NAME", "postgres")
    if "supabase.com" in host:
        project_id = name.split(".")[-1] if "." in name else name
        if project_id not in user:
            user = f"{user}.{project_id}"
        name = "postgres"
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


engine       = create_engine(_build_db_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """pgvector 확장 활성화 → patent_corpus 테이블 생성 → HNSW 인덱스 생성"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # HNSW 인덱스 (코사인 거리) — 대용량 ANN 검색 가속
    # ef_construction=64: 인덱스 품질 (높을수록 정확, 느림)
    # m=16: 그래프 연결 수 (높을수록 정확, 메모리 증가)
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS patent_corpus_embedding_hnsw "
            "ON patent_corpus USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 64)"
        ))
        conn.commit()
