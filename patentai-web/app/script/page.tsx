'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

const scripts = [
  {
    id: 'intro',
    label: '전체 소개',
    title: 'PatentAI 전체 소개 스크립트',
    content: `안녕하세요. 저희 팀은 AI 기반 지식재산 상담 시스템 PatentAI를 개발했습니다.

PatentAI는 특허 출원의 전 과정을 5개의 AI 에이전트로 자동화합니다.

기존에는 발명자가 변리사를 찾아가 수백만 원의 비용을 내고 수주를 기다려야 했습니다.
PatentAI를 사용하면 발명 아이디어만 있으면 AI가 10분 내에 명세서 초안과 특허 도면을 자동 생성해 드립니다.

저희 시스템은 총 5개의 에이전트로 구성됩니다.

첫째, 특허 상담 에이전트 — 발명 내용을 AI가 구조화합니다.
둘째, 선행기술 조사 에이전트 — 전 세계 특허 DB를 벡터 검색으로 탐색합니다.
셋째, 명세서 작성 에이전트 — sLLM으로 청구항을 자동 생성합니다.
넷째, 도면 자동 생성 에이전트 — 특허청 수준의 SVG 도면을 30초 내 생성합니다.
다섯째, 심사 대응 에이전트 — 거절이유를 분석하고 의견서 초안을 작성합니다.`,
  },
  {
    id: 'drawing',
    label: '도면 에이전트',
    title: '도면 에이전트 발표 스크립트',
    content: `저는 PatentAI의 도면 자동 생성 에이전트를 담당했습니다.

특허 출원에서 도면은 발명의 구조와 동작 방식을 시각적으로 표현하는 핵심 요소입니다.
기존에는 도면사나 변리사가 수작업으로 그려야 했고, 이 과정에 수십만 원의 비용이 발생했습니다.

저희 도면 에이전트는 명세서 텍스트만 입력하면 30초~2분 내에 도면을 자동 생성합니다.

동작 방식을 설명드리겠습니다.

첫 번째, 명세서 텍스트에서 구성요소와 처리 흐름을 GPT-4o-mini로 자동 추출합니다.
두 번째, 발명 유형에 따라 블록도·흐름도·시퀀스 다이어그램 등 5종 중 최적 유형을 자동 선택합니다.
세 번째, Python 기반 SVG 직접 렌더러로 도면부호와 연결선을 자동 배치합니다.
네 번째, 100점 만점의 품질 점수를 자동 산출하고 75점 미만이면 자동 보정을 수행합니다.

특허청 도면 기준을 완전히 준수합니다.
흑백 선화, 도면부호 표기, 여백·선 굵기 기준을 모두 자동으로 적용합니다.

실제 성능을 보시면, 저희 테스트에서 평균 품질 점수 85점, A등급을 달성했습니다.
지금 도면 갤러리에서 실제 생성된 도면 샘플 8개를 확인하실 수 있습니다.

기술 스택은 Python, GPT-4o-mini, SVG 직접 렌더링, cairosvg를 사용했습니다.
외부 다이어그램 라이브러리 없이 순수 Python으로 SVG를 직접 생성한 것이 핵심 기술입니다.`,
  },
  {
    id: 'pipeline',
    label: '전체 파이프라인',
    title: '전체 파이프라인 연동 스크립트',
    content: `PatentAI의 가장 큰 특징은 5개 에이전트가 하나의 파이프라인으로 연결된다는 점입니다.

사용자가 상담 에이전트에 발명을 설명하면,
구조화된 발명 데이터가 Supabase DB에 저장됩니다.

선행기술 조사 에이전트가 KIPRIS API로 관련 특허를 수집하고
벡터 유사도 검색으로 신규성 위험을 파악합니다.

명세서 에이전트가 선행기술 결과를 반영하여
RunPod의 EXAONE sLLM API를 호출해 청구항을 생성합니다.

청구항 생성이 완료되면 상담 앱 사이드바에 도면 생성 버튼이 활성화됩니다.
버튼을 클릭하면 도면 에이전트가 자동 실행되어 SVG 도면이 생성됩니다.

이 전체 과정이 하나의 Streamlit 앱(app.py)에서 통합 실행됩니다.
저는 도면 에이전트(drawing_agent.py)를 개발하고 app.py 파이프라인에 연결하는 작업을 담당했습니다.`,
  },
  {
    id: 'tech',
    label: '기술 스택',
    title: '기술 스택 Q&A 대응 스크립트',
    content: `[예상 질문] 왜 기존 다이어그램 라이브러리를 사용하지 않았나요?

Mermaid, draw.io 등 기존 라이브러리를 사용하면 특허청 도면 기준을 정확히 맞추기 어렵습니다.
특허 도면은 도면부호 위치, 인출선 방향, 흑백 선화 등 엄격한 기준이 있습니다.
그래서 Python으로 SVG 좌표를 직접 계산하고 태그를 생성하는 독자적인 렌더러를 구현했습니다.

[예상 질문] GPT를 쓰면 비용이 많이 들지 않나요?

도면 생성 시 GPT-4o-mini를 사용합니다. 1회 도면 생성 비용은 약 0.01달러 수준으로 매우 저렴합니다.
명세서 분석에만 LLM을 사용하고, 실제 도면 렌더링은 순수 Python으로 처리하여 비용을 최소화했습니다.

[예상 질문] 품질 검증은 어떻게 하나요?

도면부호 완비 여부, 구성요소 수, 렌더러 메타데이터를 자동으로 채점합니다.
100점 만점에서 75점을 통과 기준으로 설정했으며, 미달 시 LLM 기반 자동 보정을 1회 수행합니다.
Vision 검수 옵션을 사용하면 GPT-4o가 실제 도면 이미지를 보고 누락 요소를 감지합니다.`,
  },
  {
    id: 'demo',
    label: '데모 시연 가이드',
    title: '데모 시연 순서',
    content: `1단계 — 상담 에이전트 시작 (localhost:8501)
   - "딥러닝 기반 이미지 분류 시스템을 발명했습니다"로 시작
   - AI가 단계별 질문으로 발명 내용을 수집하는 모습 시연
   - 완성도 게이지가 100%에 도달하면 다음 단계 진행

2단계 — 선행기술 조사
   - 청구항 기반 검색어 자동 생성 확인
   - KIPRIS 검색 결과와 유사도 점수 확인
   - "신규성 확보" 또는 "주의 필요" 결과 표시

3단계 — 청구항 생성
   - RunPod sLLM API 호출
   - 독립항 1개 + 종속항 2~3개 자동 생성 확인

4단계 — 도면 자동 생성 (핵심 데모)
   - 사이드바 "특허 도면 자동 생성" 버튼 클릭
   - 30초~1분 내 SVG 도면 생성 확인
   - 블록도 + 흐름도 2개 생성, 품질 점수 표시
   - SVG 파일 다운로드 시연

5단계 — 웹 UI 소개 (localhost:3000)
   - 도면 갤러리 (/gallery) — 실제 생성 도면 8개 전시
   - 서비스 소개 페이지 — 5개 에이전트 탭 전환
   - FAQ 114개 — 카테고리 필터·검색 시연`,
  },
]

export default function ScriptPage() {
  const [active, setActive] = useState('intro')
  const s = scripts.find(x => x.id === active)!

  return (
    <div className="site">
      <style>{`
        .script-layout { display:grid; grid-template-columns:220px 1fr; min-height:600px; }
        .script-sidebar { background:#F7F6F3; border-right:1px solid #E0DDD8; padding:2rem 0; }
        .script-tab {
          display:block; width:100%; text-align:left; background:none; border:none;
          padding:.75rem 1.8rem; font-size:.82rem; color:#666; cursor:pointer;
          font-family:inherit; border-left:2px solid transparent; transition:.12s;
        }
        .script-tab:hover { color:#0A0A16; background:rgba(0,0,0,.02); }
        .script-tab.active { color:#C9A84C; font-weight:700; border-left-color:#C9A84C; background:white; }
        .script-content { padding:3rem 4rem; }
        .script-title { font-family:'Noto Serif KR',serif; font-size:1.5rem; font-weight:300; color:#0A0A16; margin-bottom:2rem; padding-bottom:1rem; border-bottom:1px solid #E8E4DC; }
        .script-body {
          font-size:.9rem; color:#333; line-height:2.2; white-space:pre-line;
          word-break:keep-all; background:#F7F6F3;
          padding:2rem; border-left:3px solid #C9A84C;
        }
        .script-actions { display:flex; gap:.8rem; margin-top:1.5rem; }
        .copy-btn { padding:.6rem 1.4rem; border:1px solid #E8E4DC; background:white; font-size:.78rem; color:#444; cursor:pointer; transition:.15s; font-family:inherit; }
        .copy-btn:hover { border-color:#C9A84C; color:#C9A84C; }
        @media(max-width:768px){ .script-layout { grid-template-columns:1fr; } .script-content { padding:2rem 1.5rem; } }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">PRESENTATION SCRIPT</div>
        <h1>발표 스크립트</h1>
        <p>PatentAI 각 에이전트 설명 및 데모 시연 가이드</p>
      </div>

      <div className="script-layout">
        <div className="script-sidebar">
          <div style={{ padding:'0 1.8rem .8rem', fontSize:'.62rem', fontWeight:700, letterSpacing:'.2em', color:'#C9A84C' }}>SCRIPTS</div>
          {scripts.map(s => (
            <button
              key={s.id}
              className={`script-tab ${active === s.id ? 'active' : ''}`}
              onClick={() => setActive(s.id)}
            >
              {s.label}
            </button>
          ))}
        </div>

        <div className="script-content">
          <div className="script-title">{s.title}</div>
          <div className="script-body">{s.content}</div>
          <div className="script-actions">
            <button
              className="copy-btn"
              onClick={() => navigator.clipboard.writeText(s.content).then(() => alert('복사됐습니다!'))}
            >
              클립보드 복사
            </button>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
