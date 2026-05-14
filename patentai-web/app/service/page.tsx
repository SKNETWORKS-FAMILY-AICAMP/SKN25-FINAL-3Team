'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'
import { useState } from 'react'

const services = [
  {
    num: '01', href: '/service/consultation',
    tag: 'CONSULTATION', title: '특허 상담 에이전트', summary: '발명 내용을 AI가 구조화',
    desc: '문제점·해결수단·효과·구성요소를 단계별로 수집하는 대화형 AI 에이전트. PDF·HWP 파일 업로드도 지원합니다.',
    steps: ['발명 내용 자유 입력', 'AI 자동 구조화', '알고리즘 단계 수집', '발명 요약 저장'],
    output: '발명 구조화 JSON · 상담 리포트 · Supabase DB 저장', time: '5–10분',
  },
  {
    num: '02', href: '/service/prior-art',
    tag: 'PRIOR ART', title: '선행기술 조사 에이전트', summary: '전 세계 특허 DB 자동 분석',
    desc: 'KIPRIS·USPTO·EPO를 벡터 유사도 검색으로 탐색하여 신규성·진보성 위험을 사전에 파악합니다.',
    steps: ['키워드·IPC 자동 추출', 'DB 대량 수집', '벡터 유사도 분석', '위험도 리포트 생성'],
    output: '유사 특허 TOP-N · 유사도 점수 · 위험도 등급', time: '2–5분',
  },
  {
    num: '03', href: '/service/specification',
    tag: 'SPECIFICATION', title: '명세서 작성 에이전트', summary: 'sLLM으로 청구항 자동 초안',
    desc: '특허 데이터로 파인튜닝한 EXAONE sLLM이 독립항·종속항·발명의 설명·실시예를 자동 작성합니다.',
    steps: ['상담 데이터 분석', '청구항 자동 생성 (sLLM)', '발명의 설명 초안화', '특허청 형식 출력'],
    output: '청구항 · 발명의 설명 · 실시예 초안', time: '3–7분',
  },
  {
    num: '04', href: '/service/drawing',
    tag: 'DRAWING AGENT', title: '도면 자동 생성 에이전트', summary: '특허청 기준 SVG 도면 생성',
    desc: '명세서 텍스트만으로 블록도·흐름도·시퀀스·상태도 등 5종 도면을 자동 생성. 품질 점수 A등급 달성.',
    steps: ['구성요소 자동 추출', '도면 유형 자동 분류', 'SVG 직접 렌더링', '품질 자동 검증'],
    output: 'SVG 벡터 도면 · PNG 고해상도 · 품질 리포트', time: '30초–2분',
  },
  {
    num: '05', href: '/service/review',
    tag: 'EMBODIMENT', title: '발설 에이전트', summary: '발명의 설명·실시예 자동 생성',
    desc: 'GPT-4o-mini가 도면 fig_json과 청구항을 결합하여 명세서의 발명의 설명·실시예 섹션을 자동 작성합니다.',
    steps: ['도면 결과 + 청구항 입력', '도면부호 자동 참조', '실시예 2~5단락 생성', '최종 페이로드 통합'],
    output: '발명의 설명 초안 · 실시예 · 도면 간단 설명', time: '2–3분',
  },
]

export default function ServicePage() {
  const { lang } = useLang()
  const [active, setActive] = useState(0)
  const s = services[active]

  return (
    <div className="site">
      <style>{`
        .svc-tabs { display:flex; border-bottom:1px solid #E0DDD8; overflow-x:auto; padding:0 3rem; }
        .svc-tab {
          padding:1rem 1.5rem; border:none; background:none; cursor:pointer;
          font-family:inherit; font-size:.78rem; font-weight:600; color:#888;
          border-bottom:2px solid transparent; white-space:nowrap; transition:.15s;
        }
        .svc-tab:hover { color:#0A0A16; }
        .svc-tab.active { color:#C9A84C; border-bottom-color:#C9A84C; }
        .svc-tab-num { font-family:'Noto Serif KR',serif; font-size:.68rem; margin-right:.35rem; color:#C9A84C; }

        .svc-detail { display:grid; grid-template-columns:1fr 1fr; min-height:500px; }
        .svc-left { padding:3.5rem 3rem; border-right:1px solid #E0DDD8; }
        .svc-right { padding:3.5rem 3rem; background:#F7F6F3; }

        .svc-tag { color:#C9A84C; font-size:.65rem; font-weight:700; letter-spacing:.28em; margin-bottom:.8rem; }
        .svc-title { font-family:'Noto Serif KR',serif; font-size:2rem; font-weight:200; color:#0A0A16; margin-bottom:.5rem; letter-spacing:-.01em; }
        .svc-summary { font-size:.95rem; color:#999; margin-bottom:1.5rem; }
        .svc-desc { font-size:.9rem; color:#444; line-height:1.9; word-break:keep-all; margin-bottom:2rem; }

        .svc-steps { display:flex; flex-direction:column; gap:1px; background:#E0DDD8; margin-bottom:1.5rem; }
        .svc-step { display:flex; align-items:center; gap:.8rem; padding:.75rem 1rem; background:white; }
        .svc-step-n { font-family:'Noto Serif KR',serif; font-size:.68rem; color:#C9A84C; width:20px; flex-shrink:0; }
        .svc-step-t { font-size:.84rem; color:#222; }
        .svc-step-arrow { margin-left:auto; color:#E0DDD8; font-size:.8rem; }

        .svc-meta-row { display:flex; gap:2rem; padding-top:1.2rem; border-top:1px solid #E8E4DC; }
        .svc-meta-label { font-size:.62rem; font-weight:700; letter-spacing:.15em; color:#C9A84C; margin-bottom:.2rem; text-transform:uppercase; }
        .svc-meta-value { font-size:.82rem; color:#333; }

        .svc-section-label { font-size:.65rem; font-weight:700; letter-spacing:.2em; color:#888; margin-bottom:.8rem; text-transform:uppercase; }
        .svc-output-box { background:white; border:1px solid #E8E4DC; padding:1rem 1.2rem; font-size:.85rem; color:#444; line-height:1.8; margin-bottom:1.5rem; word-break:keep-all; }

        .svc-actions { display:flex; gap:.6rem; flex-wrap:wrap; }
        .svc-btn { padding:.65rem 1.3rem; font-size:.76rem; font-weight:700; letter-spacing:.05em; cursor:pointer; text-decoration:none; transition:.15s; display:inline-block; border:1px solid; font-family:inherit; }
        .svc-btn-primary { background:#111128; border-color:#111128; color:#C9A84C; }
        .svc-btn-primary:hover { background:#C9A84C; color:#111128; border-color:#C9A84C; }
        .svc-btn-outline { background:white; border-color:#E8E4DC; color:#444; }
        .svc-btn-outline:hover { border-color:#C9A84C; color:#C9A84C; }

        .pipeline-bar { display:flex; align-items:stretch; background:#08081A; overflow-x:auto; }
        .pipeline-item { flex:1; min-width:120px; padding:1.5rem 1rem; border-right:1px solid rgba(255,255,255,.04); cursor:pointer; transition:.15s; text-align:center; }
        .pipeline-item:last-child { border-right:none; }
        .pipeline-item:hover, .pipeline-item.active { background:rgba(201,168,76,.08); }
        .pipeline-item.active .pi-label { color:#C9A84C; }
        .pi-num { font-family:'Noto Serif KR',serif; color:#333355; font-size:.65rem; font-weight:300; margin-bottom:.3rem; }
        .pi-label { color:#666688; font-size:.76rem; font-weight:600; transition:color .15s; }

        .img-preview { background:white; border:1px solid #E8E4DC; padding:.4rem; margin-bottom:.6rem; }
        .img-preview img { width:100%; height:auto; display:block; }

        @media(max-width:900px){
          .svc-detail { grid-template-columns:1fr; }
          .svc-right { border-top:1px solid #E0DDD8; }
          .svc-tabs { padding:0 1rem; }
        }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">{tr(t.service.tag, lang)}</div>
        <h1>{tr(t.service.h1, lang).split('\n').map((l, i) => <span key={i}>{l}{i === 0 && <br />}</span>)}</h1>
        <p>5개 AI 에이전트가 특허 출원의 전 과정을 자동화합니다</p>
      </div>

      {/* 파이프라인 바 */}
      <div className="pipeline-bar">
        {services.map((svc, i) => (
          <div key={svc.num} className={`pipeline-item ${active === i ? 'active' : ''}`} onClick={() => setActive(i)}>
            <div className="pi-num">{svc.num}</div>
            <div className="pi-label">{svc.title}</div>
          </div>
        ))}
      </div>

      {/* 탭 */}
      <div style={{ background:'white' }}>
        <div className="svc-tabs">
          {services.map((svc, i) => (
            <button key={svc.num} className={`svc-tab ${active === i ? 'active' : ''}`} onClick={() => setActive(i)}>
              <span className="svc-tab-num">{svc.num}</span>{svc.title}
            </button>
          ))}
        </div>
      </div>

      {/* 상세 */}
      <div className="svc-detail" style={{ background:'white' }}>
        <div className="svc-left">
          <div className="svc-tag">{s.tag}</div>
          <div className="svc-title">{s.title}</div>
          <div className="svc-summary">{s.summary}</div>
          <div className="svc-desc">{s.desc}</div>

          <div className="svc-section-label">처리 단계</div>
          <div className="svc-steps">
            {s.steps.map((step, i) => (
              <div key={i} className="svc-step">
                <span className="svc-step-n">0{i+1}</span>
                <span className="svc-step-t">{step}</span>
                {i < s.steps.length - 1 && <span className="svc-step-arrow">↓</span>}
              </div>
            ))}
          </div>

          <div className="svc-meta-row">
            <div><div className="svc-meta-label">처리 시간</div><div className="svc-meta-value">{s.time}</div></div>
            <div><div className="svc-meta-label">유형</div><div className="svc-meta-value">{s.tag}</div></div>
          </div>
        </div>

        <div className="svc-right">
          <div className="svc-section-label">Output</div>
          <div className="svc-output-box">{s.output}</div>

          {s.num === '04' && (
            <>
              <div className="svc-section-label">도면 샘플</div>
              <div className="img-preview">
                <img src="/drawings/sample_block.svg" alt="블록도 샘플" />
              </div>
              <div className="img-preview">
                <img src="/drawings/sample_flow.svg" alt="흐름도 샘플" />
              </div>
            </>
          )}

          <div className="svc-actions">
            <Link href={s.href} className="svc-btn svc-btn-primary">상세 보기 →</Link>
            {s.num === '04' && <Link href="/gallery" className="svc-btn svc-btn-outline">도면 갤러리</Link>}
            <Link href="/contact" className="svc-btn svc-btn-outline">상담 신청</Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
