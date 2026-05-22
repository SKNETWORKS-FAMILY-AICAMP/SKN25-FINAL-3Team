# PatentAI 웹 UI (patentai-web)

특허 출원 서비스를 위한 Next.js 기반 홈페이지입니다.

## 담당자

- **bizseohyunkim** (김서현) — 웹 UI, 도면 에이전트, 발명의 설명 에이전트

---

## 기술 스택

| 항목 | 기술 |
|---|---|
| 프레임워크 | Next.js 16 (App Router) |
| 언어 | TypeScript |
| 스타일 | Tailwind CSS + Custom CSS |
| 폰트 | Noto Serif KR, Noto Sans KR |

---

## 설치 및 실행

```bash
cd patentai-web
npm install
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

---

## 페이지 구성

| 경로 | 파일 | 설명 |
|---|---|---|
| `/` | `app/page.tsx` | 홈 — 메인 히어로 슬라이드, 주요 서비스, 업무 흐름 |
| `/service` | `app/service/page.tsx` | 서비스 소개 — 핵심 서비스, 차별점 |
| `/team` | `app/team/page.tsx` | 구성원 소개 |
| `/news` | `app/news/page.tsx` | 소식/자료 — 카드뉴스 |

---

## 폴더 구조

```
patentai-web/
├── app/
│   ├── globals.css        # 전체 CSS 스타일
│   ├── layout.tsx         # 공통 레이아웃
│   ├── page.tsx           # 홈 페이지
│   ├── service/page.tsx   # 서비스 소개
│   ├── team/page.tsx      # 구성원
│   └── news/page.tsx      # 소식/자료
└── components/
    ├── Nav.tsx            # 네비게이션 바
    └── Footer.tsx         # 푸터
```

---

## 디자인 시스템

| 항목 | 값 |
|---|---|
| 배경 (다크) | `#0A0A16` |
| 배경 (라이트) | `#F5F4F1` |
| 포인트 색상 | `#C9A84C` (골드) |
| 시스템 색상 | `#111128` |
| 폰트 (제목) | Noto Serif KR |
| 폰트 (본문) | Noto Sans KR |

---

## 주요 기능

- **메인 히어로 슬라이드** — 경복궁 / N서울타워 / 롯데월드타워 5초 간격 자동 전환
- **반응형 레이아웃** — 모바일(900px 이하) 대응
- **현재 페이지 하이라이트** — 네비게이션 활성 메뉴 골드색 표시
- **카드 호버 효과** — 서비스 카드 마우스 오버 시 상승 애니메이션

---

## 에이전트 연동 계획

```
고객 상담 입력
    ↓
상담 에이전트 → 선행기술 조사 → 청구항 생성
    ↓
도면 에이전트 → SVG/PNG 도면
    ↓
발명의 설명 에이전트
    ↓
웹 UI에서 결과 표시  ← 이 파일
```

FastAPI 백엔드 완성 후 `/api/` 엔드포인트 연동 예정

---

## 향후 작업 예정

- [ ] 고객 로그인 / 직원 로그인 페이지
- [ ] 상담 입력 → 에이전트 파이프라인 연동 페이지
- [ ] 도면 결과 표시 UI
- [ ] 최종 명세서 다운로드 기능
