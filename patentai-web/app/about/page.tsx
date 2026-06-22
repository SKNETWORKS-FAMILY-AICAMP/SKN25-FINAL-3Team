'use client'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function AboutPage() {
  const { lang } = useLang()
  const a = t.about

  const values = [
    { num:'01', title: tr(a.v1t, lang), desc: tr(a.v1d, lang) },
    { num:'02', title: tr(a.v2t, lang), desc: tr(a.v2d, lang) },
    { num:'03', title: tr(a.v3t, lang), desc: tr(a.v3d, lang) },
    { num:'04', title: tr(a.v4t, lang), desc: tr(a.v4d, lang) },
  ]

  const pipeline = [tr(a.ps1,lang), tr(a.ps2,lang), tr(a.ps3,lang), tr(a.ps4,lang), tr(a.ps5,lang)]

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
        <div className="tag">{tr(a.tag, lang)}</div>
        <h1>{tr(a.h1, lang)}</h1>
        <p>{tr(a.desc, lang).split('\n').map((l, i) => <span key={i}>{l}{i === 0 && <br />}</span>)}</p>
      </div>

      <div className="section">
        <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:'1px', background:'#E0DDD8', marginBottom:'4rem' }}>
          {[
            { num:'6',    label: tr(a.stat1, lang) },
            { num:'5',    label: tr(a.stat2, lang) },
            { num:'301+', label: tr(a.stat3, lang) },
            { num:'2026', label: tr(a.stat4, lang) },
          ].map(s => (
            <div key={s.label} className="about-stat">
              <div className="about-stat-num">{s.num}</div>
              <div className="about-stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="line"></div>
        <div className="title">{tr(a.missionTitle, lang)}</div>
        <div className="sub">{tr(a.missionSub, lang)}</div>

        <div className="about-grid">
          {values.map(v => (
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
        <div className="title">{tr(a.pipelineTitle, lang)}</div>
        <div className="sub">{tr(a.pipelineSub, lang)}</div>
        <div className="workflow">
          {pipeline.map((s, i) => (
            <div key={s} className="step">
              <b>0{i+1}</b>
              <p>{s}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section" style={{ textAlign:'center' }}>
        <div className="title">{tr(a.ctaTitle, lang)}</div>
        <div className="sub">{tr(a.ctaSub, lang)}</div>
        <Link href="/contact" style={{
          display:'inline-block', padding:'1rem 3rem',
          border:'1px solid #C9A84C', color:'#C9A84C',
          fontSize:'.82rem', fontWeight:700, letterSpacing:'.1em',
        }}>{tr(a.ctaBtn, lang)}</Link>
      </div>

      <Footer />
    </div>
  )
}
