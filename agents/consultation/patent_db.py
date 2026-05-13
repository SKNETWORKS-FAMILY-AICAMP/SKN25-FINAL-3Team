import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

_ENV_DIR = Path(__file__).resolve().parent
load_dotenv(_ENV_DIR.parents[1] / ".env")
load_dotenv(_ENV_DIR / ".env", override=True)

Base = declarative_base()


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
    embedding     = Column(JSON)          # list[float] — text-embedding-3-small (1536-dim)


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
    """patent_corpus 테이블이 없으면 생성합니다."""
    Base.metadata.create_all(bind=engine)
