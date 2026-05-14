'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export default function Page() {
  return (
    <div className="site">
      <style>{`
        .det-section{margin-bottom:3rem;padding-bottom:3rem;border-bottom:1px solid #E8E4DC;}
        .det-kicker{font-size:.65rem;font-weight:700;letter-spacing:.3em;color:#C9A84C;margin-bottom:.6rem;}
        .det-h2{font-family:'Noto Serif KR',serif;font-size:1.6rem;font-weight:300;color:#0A0A16;margin-bottom:1rem;}
        .det-p{font-size:.9rem;color:#444;line-height:2;word-break:keep-all;margin-bottom:1rem;}
        .det-list{list-style:none;padding:0;display:flex;flex-direction:column;gap:.5rem;margin-bottom:1.2rem;}
        .det-list li{display:flex;gap:.7rem;font-size:.88rem;color:#333;line-height:1.7;}
        .det-list li::before{content:'—';color:#C9A84C;flex-shrink:0;}
        .det-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#E0DDD8;margin:1.2rem 0;}
        .det-cell{background:white;padding:1.2rem;}
        .det-cell-label{font-size:.62rem;font-weight:700;letter-spacing:.15em;color:#C9A84C;margin-bottom:.3rem;}
        .det-cell-value{font-size:.86rem;color:#222;line-height:1.7;word-break:keep-all;}
        .det-step{display:flex;gap:1rem;margin-bottom:1rem;}
        .det-step-num{width:34px;height:34px;border:1px solid rgba(201,168,76,.3);display:flex;align-items:center;justify-content:center;font-family:'Noto Serif KR',serif;color:#C9A84C;font-size:.78rem;flex-shrink:0;}
        .det-step-title{font-weight:700;font-size:.88rem;color:#0A0A16;margin-bottom:.3rem;}
        .det-step-desc{font-size:.83rem;color:#555;line-height:1.8;word-break:keep-all;}
        .qa-item{border:1px solid #E8E4DC;margin-bottom:.5rem;}
        .qa-q{font-size:.88rem;font-weight:700;color:#0A0A16;padding:1rem 1.2rem;}
        .qa-a{font-size:.83rem;color:#555;line-height:1.85;padding:.2rem 1.2rem 1rem;word-break:keep-all;}
        @media(max-width:900px){.det-grid{grid-template-columns:1fr;}}
      `}</style>
      <Nav />
      <div className="hero">
        <div className="tag">05 — PATENT REVIEW</div>
        <h1>심사 대응<br/>에이전트</h1>
        <p>특허청 거절이유를 AI가 분석하고 의견서·보정서 초안을 자동 생성합니다.</p>
      </div>
      <div style={{ padding:'3.5rem 6rem', maxWidth:900, margin:'0 auto' }}>
        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">심사 대응 에이전트란?</div>
          <div className="det-p">특허청 심사관의 거절이유 통지서(OA, Office Action)를 AI가 자동 파싱하고 거절 유형을 분류하여 대응 전략과 의견서·보정서 초안을 제안합니다.</div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">AI 모델</div><div className="det-cell-value">GPT-4o (문서 분석·초안 생성)</div></div>
            <div className="det-cell"><div className="det-cell-label">처리 시간</div><div className="det-cell-value">2–4분</div></div>
            <div className="det-cell"><div className="det-cell-label">지원 거절 유형</div><div className="det-cell-value">신규성·진보성·기재불비·선행기술</div></div>
            <div className="det-cell"><div className="det-cell-label">출력</div><div className="det-cell-value">의견서 초안 · 보정 전략 · 청구항 보정 제안</div></div>
          </div>
        </div>
        <div className="det-section">
          <div className="det-kicker">HOW IT WORKS</div>
          <div className="det-h2">동작 원리</div>
          {[
            { n:'01', title:'OA 문서 파싱', desc:'특허청 거절이유 통지서를 텍스트로 입력받아 거절 항목·인용 선행기술·거절 이유를 자동으로 추출합니다.' },
            { n:'02', title:'거절 유형 분류', desc:'신규성 결여(특허법 제29조 제1항), 진보성 결여(제29조 제2항), 기재불비(제42조), 선행기술 결합 등 유형별로 자동 분류합니다.' },
            { n:'03', title:'대응 전략 제안', desc:'각 거절 유형에 맞는 대응 방향을 제안합니다. 신규성 문제는 청구범위 한정, 진보성 문제는 차별점 강조, 기재불비는 명세서 보완 방향을 안내합니다.' },
            { n:'04', title:'의견서·보정서 초안 생성', desc:'특허청 제출 형식에 맞는 의견서 초안과 청구항 보정 제안을 자동 생성합니다.' },
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>
        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            { q:'거절이유 통지서 없이도 사용할 수 있나요?', a:'심사 대응 에이전트는 거절이유 통지서 수신 후 사용하는 것이 주 목적입니다. 다만 출원 전 선행기술 조사 결과를 기반으로 예상 거절이유에 대한 사전 대응 전략도 제공합니다.' },
            { q:'AI 의견서를 바로 제출할 수 있나요?', a:'AI가 생성하는 의견서는 고품질 초안입니다. 법적 효력이 있는 의견서 제출은 전문 변리사가 최종 검토·서명 후 진행해야 합니다.' },
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>
        <div style={{ display:'flex', gap:'1rem' }}>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2rem', background:'#111128', border:'1px solid #111128', color:'#C9A84C', fontSize:'.8rem', fontWeight:700 }}>상담 신청하기 →</Link>
          <Link href="/service" style={{ display:'inline-block', padding:'.85rem 2rem', border:'1px solid #E8E4DC', color:'#444', fontSize:'.8rem' }}>서비스 전체 보기</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
