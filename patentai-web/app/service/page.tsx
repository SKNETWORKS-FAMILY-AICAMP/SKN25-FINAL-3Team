'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

const services = [
  {
    num: '01',
    title: '특허 상담 에이전트',
    tag: 'CONSULTATION',
    summary: '발명 내용을 AI가 구조화하여 특허 출원에 필요한 핵심 정보를 체계적으로 정리합니다.',
    steps: [
      '발명자가 자유롭게 발명 내용 설명',
      'AI가 문제점·해결수단·효과·구성요소 추출',
      '알고리즘 단계 수집 및 청구항 초안 생성',
      '최종 발명 요약 확인 및 저장',
    ],
    output: '발명 구조화 JSON · 청구항 초안 · 상담 리포트',
  },
  {
    num: '02',
    title: '선행기술 조사',
    tag: 'PRIOR ART',
    summary: 'KIPRIS 특허 데이터베이스 기반 벡터 유사도 검색으로 신규성·진보성 위험을 빠르게 파악합니다.',
    steps: [
      '발명 키워드 및 청구항 기반 검색어 생성',
      'KIPRIS IPC 코드별 대량 특허 수집',
      '임베딩 유사도 + 키워드 하이브리드 검색',
      '유사 특허 TOP-N 랭킹 및 위험도 리포트 생성',
    ],
    output: '유사 특허 목록 · 유사도 점수 · 신규성 위험 리포트',
  },
  {
    num: '03',
    title: '명세서 작성',
    tag: 'SPECIFICATION',
    summary: '청구항·발명의 설명·실시예·도면 설명을 AI가 자동으로 초안화하여 출원 준비 시간을 단축합니다.',
    steps: [
      '상담 데이터 기반 청구항 자동 생성 (sLLM)',
      '발명의 설명 · 실시예 자동 작성',
      '도면 설명 및 부호 설명 생성',
      '특허청 표준 형식 문서 출력',
    ],
    output: '청구항 · 발명의 설명 · 실시예 · 도면 설명 초안',
  },
  {
    num: '04',
    title: '도면 자동 생성',
    tag: 'DRAWING',
    summary: '명세서 텍스트를 분석하여 특허청 실무 수준의 블록도·흐름도·시퀀스 다이어그램을 자동 생성합니다.',
    steps: [
      '명세서에서 구성요소 및 처리 흐름 추출',
      '도면 유형 자동 분류 (블록도/흐름도/시퀀스 등)',
      'SVG 직접 렌더링 (도면부호 포함)',
      '품질 점수 산출 및 자동 보정',
    ],
    output: 'SVG 도면 · PNG 변환본 · 품질 리포트',
  },
  {
    num: '05',
    title: '심사 대응',
    tag: 'REVIEW',
    summary: '거절이유를 AI가 분석하고 의견서 작성 방향 및 보정 전략을 제안합니다.',
    steps: [
      '심사관 거절이유 통지서 파싱',
      '거절 유형 분류 (신규성/진보성/기재불비)',
      '대응 전략 및 의견서 초안 제안',
      '보정 항목 및 범위 권고',
    ],
    output: '의견서 초안 · 보정 전략 리포트',
  },
]

export default function ServicePage() {
  const { lang } = useLang()
  const sv = t.service
  return (
    <div className="site">
      <style>{`
        .service-detail {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.5rem;
          margin-top: 3rem;
        }
        .service-card-detail {
          background: white;
          border: 1px solid #E8E4DC;
          padding: 2rem;
          box-shadow: 0 8px 24px rgba(0,0,0,0.05);
          transition: 0.2s;
        }
        .service-card-detail:hover {
          transform: translateY(-4px);
          box-shadow: 0 16px 36px rgba(0,0,0,0.09);
          border-color: rgba(201,168,76,0.4);
        }
        .service-num { color: #C9A84C; font-family: 'Noto Serif KR', serif; font-size: 1.6rem; font-weight: 300; }
        .service-tag { color: #C9A84C; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.2em; margin: 0.3rem 0 0.8rem; }
        .service-title { font-size: 1.15rem; font-weight: 700; color: #111128; margin-bottom: 0.7rem; }
        .service-summary { color: #555; font-size: 0.88rem; line-height: 1.75; margin-bottom: 1.2rem; }
        .service-steps { list-style: none; padding: 0; margin: 0 0 1.2rem; }
        .service-steps li {
          font-size: 0.84rem; color: #444; padding: 0.4rem 0;
          border-bottom: 1px solid #F0EDE6;
          display: flex; align-items: flex-start; gap: 0.6rem;
        }
        .service-steps li::before { content: '→'; color: #C9A84C; flex-shrink: 0; }
        .service-output {
          background: #F5F4F1;
          padding: 0.8rem 1rem;
          font-size: 0.8rem;
          color: #666;
          border-left: 3px solid #C9A84C;
        }
        .service-output strong { color: #111128; display: block; margin-bottom: 0.2rem; font-size: 0.72rem; letter-spacing: 0.08em; }
        @media (max-width: 900px) {
          .service-detail { grid-template-columns: 1fr; }
        }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">{tr(sv.tag, lang)}</div>
        <h1>{tr(sv.h1, lang).split('\n').map((l, i) => <span key={i}>{l}{i === 0 && <br />}</span>)}</h1>
        <p>{tr(sv.tag, lang)}</p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">{tr(sv.title, lang)}</div>
        <div className="sub">{tr(sv.sub, lang)}</div>

        <div className="service-detail">
          {services.map(s => (
            <div className="service-card-detail" key={s.num}>
              <div className="service-num">{s.num}</div>
              <div className="service-tag">{s.tag}</div>
              <div className="service-title">{s.title}</div>
              <div className="service-summary">{s.summary}</div>
              <ul className="service-steps">
                {s.steps.map((step, i) => <li key={i}>{step}</li>)}
              </ul>
              <div className="service-output">
                <strong>OUTPUT</strong>
                {s.output}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '3rem', textAlign: 'center' }}>
          <Link href="/contact" style={{
            display: 'inline-block',
            padding: '1rem 3rem',
            border: '1px solid #C9A84C',
            color: '#C9A84C',
            fontSize: '0.88rem',
            fontWeight: 700,
            letterSpacing: '0.1em',
            textDecoration: 'none',
            transition: '0.2s',
          }}>
            {tr(sv.cta, lang)}
          </Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
