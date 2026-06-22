import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

Base = declarative_base()


class PatentCorpus(Base):
    __tablename__ = "patent_corpus"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    application_number = Column(String(50), unique=True) 
    register_number    = Column(String(50))
    title              = Column(Text)
    applicant          = Column(Text)
    abstract           = Column(Text)
    claim1             = Column(Text)
    ipc_codes          = Column(JSON)
    pdf_s3_url          = Column(Text)

    # 심사관 인용 선행문헌 저장
    # 에이전트 정확도 검증할 때 정답 레이블로 사용
    examiner_cited     = Column(JSON)
    embedding          = Column(Vector(1536))

database_url = os.getenv("RDS_DATABASE_URL")
if not database_url:
    raise RuntimeError("RDS_DATABASE_URL 환경 변수가 설정되어 있지 않습니다. .env 파일을 확인해주세요.")
engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS patent_corpus_embedding_index ON patent_corpus
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS patent_corpus_trgm_index ON patent_corpus
                        USING gin ((title || ' ' || abstract || ' ' || claim1) gin_trgm_ops)
        """))
        conn.commit()
