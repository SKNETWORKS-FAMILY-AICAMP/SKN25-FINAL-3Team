# SKN25-FINAL-3Team

## AI 기반 특허 작성 보조 Agent Pipeline

개인 발명가의 아이디어를 입력받아 변리사가 검토 가능한 특허 초안과 선행기술 검토 결과를 생성하는 AI Agent 기반 특허 작성 보조 시스템입니다.

특허 문서는 청구항, 도면, 명세서, 선행기술 검토가 서로 연결되어야 하며 비전문가가 직접 작성하기 어렵습니다. 본 프로젝트는 변리사의 검토 전 단계에서 초안 작성과 조사 시간을 줄이는 것을 목표로 합니다.

## 프로젝트 주요 범위

- 발명 아이디어 상담 및 요약
- 선행기술조사 및 유사 특허 검색
- 청구항 초안 생성
- 도면 초안 생성
- 명세서 초안 생성
- 심사관 관점 검토 보조

## 주요 폴더 구조

```text
agents/             AI 에이전트 코드
backend/            백엔드 서버 코드
frontend/           프론트엔드 코드
apps/               데모/검증용 앱
data/               데이터 매니페스트 및 샘플 데이터
docs/               프로젝트 문서 및 발표자료
scripts/            데이터 처리 및 개발 보조 스크립트
models/             모델 설정 및 학습 산출물 설명
notebooks/          데이터셋/모델링 실험 노트북
```

## 산출물 및 데이터 링크

### 산출물 관리 Google Drive

https://drive.google.com/drive/folders/1TcCVG8lnVapn9Fm40DdxhmhyquaMja2L

포함 내용:
- 기획 문서
- 데이터 수집 및 저장 문서
- 모델링 및 평가 문서
- 모델 배포 문서
- 발표 자료
- 멘토링/미팅 기록

### 데이터 관리 Google Drive

https://drive.google.com/drive/folders/1V-KJTNLjYpxqp_VAgIxKYQO6pm8-zMa2

포함 내용:
- IPC별 특허 PDF/TXT 데이터
- G06F/G06N/G06Q/G06V 데이터
- extracted_texts
- 학습/평가용 데이터셋

## 데이터 관리 안내

대량 특허 PDF/TXT 원천 데이터는 Google Drive에서 관리하며, GitHub에는 소스 코드, 문서, 데이터 매니페스트, 샘플 데이터 중심으로 정리합니다.

API Key, AWS 인증 정보, `.env` 파일 등 민감 정보는 GitHub에 포함하지 않습니다.
