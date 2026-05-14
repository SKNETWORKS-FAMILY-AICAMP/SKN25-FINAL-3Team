'use client'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export default function AboutPage() {
  return (
    <div className="site">
      <style>{`
        .about-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; margin-top: 3rem; }
        .about-value { border-left: 1px solid rgba(201,168,76,.3); padding: 1.5rem 2rem; }
        .about-value-num { font-family:'Noto Serif KR',serif; color:#C9A84C; font-size:0.7rem; font-weight:700; letter-spacing:.2em; margin-bottom:.6rem; }
        .about-value-title { font-family:'Noto Serif KR',serif; font-size:1.1rem; font-weight:300; color:#0A0A16; margin-bottom:.6rem; }
        .about-value-desc { font-size:.88rem; color:#666; line-height:1.85; }
        .about-stat { display:flex; flex-direction:column; align-items:center; padding:2rem; border:1px solid #E8E4DC; background:white; }
        .about-stat-num { font-family:'Noto Serif KR',serif; font-size:2.5rem; font-weight:200; color:#0A0A16; }
        .about-stat-label { font-size:.72rem; color:#999; letter-spacing:.1em; text-transform:uppercase; margin-top:.4rem; }
        @media(max-width:900px){ .about-grid { grid-template-columns:1fr; gap:2rem; } }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">ABOUT PATENTAI</div>
        <h1>PatentAI 소개</h1>
        <p>AI 기술로 특허 출원의 문턱을 낮추고,<br />모든 발명자가 권리를 보호받을 수 있는 세상을 만듭니다.</p>
      </div>

      <div className="section">
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'1px', background:'#E0DDD8', marginBottom:'4rem' }}>
          {[
            { num:'6', label:'AI 에이전트' },
            { num:'5', label:'핵심 서비스' },
            { num:'114+', label:'FAQ 데이터베이스' },
            { num:'2026', label:'설립 연도' },
          ].map(s => (
            <div key={s.label} className="about-stat">
              <div className="about-stat-num">{s.num}</div>
              <div className="about-stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="line"></div>
        <div className="title">미션 & 비전</div>
        <div className="sub">발명의 가치를 권리로 만드는 AI 기반 지식재산 상담 플랫폼</div>

        <div className="about-grid">
          {[
            { num:'01', title:'접근성', desc:'복잡한 특허 절차를 AI로 간소화하여 누구나 쉽게 발명을 권리로 보호받을 수 있도록 합니다.' },
            { num:'02', title:'전문성', desc:'특허 데이터 기반의 AI 모델과 변리사 워크플로우를 결합하여 전문가 수준의 서비스를 제공합니다.' },
            { num:'03', title:'혁신성', desc:'GPT-4o, sLLM, 벡터 검색 등 최신 AI 기술을 특허 실무에 적용하여 업계 표준을 선도합니다.' },
            { num:'04', title:'신뢰성', desc:'모든 상담 데이터는 암호화되어 보관되며, 발명자의 기밀은 철저히 보호됩니다.' },
          ].map(v => (
            <div key={v.num} className="about-value">
              <div className="about-value-num">{v.num}</div>
              <div className="about-value-title">{v.title}</div>
              <div className="about-value-desc">{v.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="section dark">
        <div className="line"></div>
        <div className="title">PatentAI 파이프라인</div>
        <div className="sub">발명 상담부터 도면 생성까지 하나의 AI 흐름으로 연결합니다.</div>
        <div className="workflow">
          {['발명 상담','선행기술 조사','명세서 작성','도면 생성','심사 대응'].map((s,i) => (
            <div key={s} className="step">
              <b>0{i+1}</b>
              <p>{s}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section" style={{ textAlign:'center' }}>
        <div className="title">함께 시작하세요</div>
        <div className="sub">PatentAI와 함께 발명의 가치를 권리로 만들어 보세요.</div>
        <Link href="/contact" style={{
          display:'inline-block', padding:'1rem 3rem',
          border:'1px solid #C9A84C', color:'#C9A84C',
          fontSize:'.82rem', fontWeight:700, letterSpacing:'.1em',
        }}>상담 신청하기 →</Link>
      </div>

      <Footer />
    </div>
  )
}
