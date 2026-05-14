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
        <div className="tag">03 — SPECIFICATION</div>
        <h1>명세서 작성<br/>에이전트</h1>
        <p>특허 데이터로 파인튜닝한 sLLM이 청구항·발명의 설명·실시예를 자동으로 초안화합니다.</p>
      </div>
      <div style={{ padding:'3.5rem 6rem', maxWidth:900, margin:'0 auto' }}>
        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">명세서 작성 에이전트란?</div>
          <div className="det-p">PatentAI 명세서 에이전트는 EXAONE-3.0-7.8B 모델을 한국 특허 데이터로 LoRA 파인튜닝한 sLLM을 활용하여 특허 명세서 초안을 자동 생성합니다. 변리사 작업 시간을 60~80% 단축합니다.</div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">AI 모델</div><div className="det-cell-value">EXAONE-3.0-7.8B + LoRA 파인튜닝</div></div>
            <div className="det-cell"><div className="det-cell-label">배포 환경</div><div className="det-cell-value">RunPod GPU 서버 (FastAPI)</div></div>
            <div className="det-cell"><div className="det-cell-label">처리 시간</div><div className="det-cell-value">3–7분</div></div>
            <div className="det-cell"><div className="det-cell-label">출력</div><div className="det-cell-value">청구항 · 발명의 설명 · 실시예 초안</div></div>
          </div>
        </div>
        <div className="det-section">
          <div className="det-kicker">HOW IT WORKS</div>
          <div className="det-h2">동작 원리</div>
          {[
            { n:'01', title:'상담 데이터 기반 청구항 생성', desc:'상담 에이전트에서 수집한 발명 구조화 데이터를 RunPod에 배포된 EXAONE sLLM API로 전송합니다. sLLM은 독립항(핵심 청구항)과 종속항(세부 한정 청구항)을 자동 생성합니다.' },
            { n:'02', title:'명세서 각 섹션 자동 작성', desc:'발명의 설명(기술분야·배경기술·발명의 내용·실시예), 도면의 간단한 설명, 부호의 설명을 특허법 제42조 형식에 맞게 자동 초안화합니다.' },
            { n:'03', title:'선행기술 반영', desc:'선행기술 조사 결과에서 식별된 유사 특허를 바탕으로 배경기술 섹션의 종래 기술 기재와 발명의 차별점을 자동으로 강조합니다.' },
            { n:'04', title:'특허청 형식 출력', desc:'특허법 시행규칙 별지 제15호 서식에 맞는 최종 명세서 문서를 생성합니다. 각 섹션 번호, 들여쓰기, 도면부호 형식을 자동 적용합니다.' },
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
            { q:'sLLM이 일반 GPT와 다른 점은 무엇인가요?', a:'sLLM은 실제 한국 특허 명세서 데이터로 파인튜닝된 소형 언어 모델입니다. 일반 GPT보다 특허 용어·형식·법적 요건을 더 잘 이해하며 청구항 구조에 특화되어 있습니다.' },
            { q:'생성된 명세서를 바로 특허청에 제출할 수 있나요?', a:'초안 품질이 높지만 전문 변리사의 최종 검토 후 제출을 권장합니다. AI 초안을 활용하면 변리사 작업 시간이 대폭 단축되어 전체 비용을 절감할 수 있습니다.' },
            { q:'소프트웨어·AI 발명도 청구항 작성이 가능한가요?', a:'네. "~를 실행하는 프로그램을 기록한 컴퓨터 판독 가능 매체" 또는 "~방법을 수행하는 시스템" 형태의 소프트웨어 발명 청구항 작성을 지원합니다.' },
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>
        <div style={{ display:'flex', gap:'1rem' }}>
          <Link href="/service/drawing" style={{ display:'inline-block', padding:'.85rem 2rem', background:'#111128', border:'1px solid #111128', color:'#C9A84C', fontSize:'.8rem', fontWeight:700 }}>다음: 도면 생성 →</Link>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2rem', border:'1px solid #E8E4DC', color:'#444', fontSize:'.8rem' }}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
