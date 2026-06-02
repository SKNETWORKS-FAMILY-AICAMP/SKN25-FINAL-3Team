# ADR-002: PostgreSQL 단일 공유 DB (pgvector)

**상태:** Accepted  
**날짜:** 2026-06-02

## 맥락

Django(인증)와 FastAPI(파이프라인)가 별도 서비스로 분리됨에 따라 DB를 어떻게 구성할지 결정이 필요했다.

후보:
1. 각 서비스가 별도 DB 인스턴스 사용
2. 단일 PostgreSQL 인스턴스를 두 서비스가 공유

## 결정

`pgvector/pgvector:pg15` 이미지를 사용하는 단일 PostgreSQL 인스턴스를 공유한다.

```
postgres:5432 / patent_ai DB
  ├── Django 관리 테이블   (accounts_user, token_blacklist_*, django_*)
  ├── FastAPI 관리 테이블  (patent_runs — Alembic으로 관리)
  └── 특허 코퍼스          (patent_corpus — pgvector 1536-dim embedding)
```

## 이유

- **팀 규모**: 5인 팀 프로젝트에서 DB를 두 개 운영하면 인프라 복잡도만 늘어난다.
- **pgvector**: 선행기술 벡터 검색에 pgvector가 필요하다. 별도 벡터 DB(Pinecone, Weaviate 등)를 추가하는 것보다 PostgreSQL 확장으로 처리하면 운영 대상이 하나로 줄어든다.
- **마이그레이션 격리**: Django는 Django ORM 마이그레이션으로, FastAPI는 Alembic으로 각자 테이블을 관리하므로 스키마 충돌이 없다.

## 결과

- DB 인스턴스가 하나이므로 장애 시 두 서비스가 동시에 영향받는다.
- Django 마이그레이션(`manage.py migrate`)과 FastAPI 마이그레이션(`alembic upgrade head`)을 각 서비스 기동 시 독립적으로 실행해야 한다.
- 프로덕션에서는 `DB_PASSWORD`를 기본값(`patent_pw`)에서 반드시 변경해야 한다.
