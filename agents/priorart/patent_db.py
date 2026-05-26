import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, JSON, text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # 프로젝트 루트의 .env 파일 로드

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

    # 심사관 인용 선행문헌 저장
    # 에이전트 정확도 검증할 때 정답 레이블로 사용
    examiner_cited     = Column(JSON)
    embedding          = Column(Vector(1536))

engine = create_engine(os.getenv("RDS_DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS patent_corpus_embedding_index ON patent_corpus
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
        """))
        conn.commit()