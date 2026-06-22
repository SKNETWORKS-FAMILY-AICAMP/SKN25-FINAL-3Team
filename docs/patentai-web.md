# PatentAI 웹 UI (patentai-web)

특허 출원 서비스를 위한 Next.js 기반 홈페이지입니다.

**담당자:** bizseohyunkim (김서현) — 웹 UI, 도면 에이전트, 발명의 설명 에이전트

---

## 기술 스택

| 항목 | 기술 |
|---|---|
| 프레임워크 | Next.js 16 (App Router) |
| 언어 | TypeScript |
| 스타일 | Custom CSS (globals.css) |
| 폰트 | Noto Serif KR, Noto Sans KR |
| 다국어 | ko / en / ja / zh (i18n 자체 구현) |
| PDF 파싱 | pdfjs-dist (클라이언트 사이드) |

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

| 경로 | 설명 |
|---|---|
| `/` | 홈 — 히어로, 서비스 소개, 업무 흐름, WHY PATENTAI 비교 |
| `/service` | 서비스 소개 — 5개 에이전트 파이프라인 탭 |
| `/service/demo` | 도면 생성 데모 — 텍스트/PDF 입력 → SVG 도면 출력 |
| `/service/consultation` | 상담 에이전트 상세 |
| `/service/prior-art` | 선행기술 에이전트 상세 |
| `/service/specification` | 명세서 에이전트 상세 |
| `/service/review` | 발설 에이전트 상세 |
| `/gallery` | 특허 도면 갤러리 — 344개, 47개 도메인, 5종 타입 필터 |
| `/faq` | FAQ — 301개 항목, 카테고리 필터, 검색 |
| `/showcase` | 쇼케이스 슬라이드 (6슬라이드, 자동 전환) |
| `/team` | 구성원 소개 + 개인 프로필 페이지 |
| `/news` | 소식/자료 |
| `/about` | PatentAI 소개 |
| `/careers` | 채용 공고 |
| `/contact` | 상담 신청 폼 |
| `/privacy` | 개인정보처리방침 |
| `/terms` | 이용약관 |
| `/login` | 고객/직원 로그인 |

---

## 도면 생성 데모 (`/service/demo`)

```
텍스트 입력 또는 PDF 업로드
    ↓
POST /api/drawings → agents/runpod/dev_server.py
    ↓
SVG 도면 렌더링 + 참조부호 테이블 표시
```

- PDF는 `pdfjs-dist`로 클라이언트에서 텍스트 추출
- 백엔드: `agents/runpod/dev_server.py` (GPT 기반 경량 서버)
- 도면 5종: 블록도·흐름도·시퀀스·화면예시도·회로도

---

## 다국어 (i18n)

- `lib/i18n.ts` — 모든 번역 키 관리 (`t` 객체)
- `contexts/LangContext.tsx` — 언어 상태 전역 관리
- 사용법:

```tsx
const { lang } = useLang()
const txt = t.sectionName
return <h1>{tr(txt.key, lang)}</h1>
```

---

## 폴더 구조

```
patentai-web/
├── app/                   # Next.js App Router 페이지
│   ├── page.tsx           # 홈
│   ├── service/           # 서비스 소개 + 데모 + 상세 페이지
│   ├── gallery/           # 도면 갤러리
│   ├── faq/               # FAQ
│   ├── showcase/          # 쇼케이스
│   ├── team/              # 팀원
│   ├── news/              # 소식
│   ├── about/             # 소개
│   ├── careers/           # 채용
│   ├── contact/           # 상담 신청
│   ├── privacy/           # 개인정보처리방침
│   ├── terms/             # 이용약관
│   └── login/             # 로그인
├── components/
│   ├── Nav.tsx            # 네비게이션
│   ├── Footer.tsx         # 푸터
│   └── CookieBanner.tsx   # 쿠키 동의 배너
├── contexts/
│   └── LangContext.tsx    # 다국어 상태
└── lib/
    └── i18n.ts            # 번역 키 (ko/en/ja/zh)
```

---

## 디자인 시스템

| 항목 | 값 |
|---|---|
| 배경 (다크) | `#0A0A16` |
| 배경 (라이트) | `#F5F4F1` |
| 포인트 색상 | `#C9A84C` (골드) |
| 폰트 (제목) | Noto Serif KR |
| 폰트 (본문) | Noto Sans KR |

---

## 에이전트 연동

```
/service/demo 페이지
    ↓ POST /api/drawings
    ↓ agents/runpod/dev_server.py
    ↓ drawing_agent.py → SVG 생성
    ↓ 웹 UI에서 결과 표시
```
