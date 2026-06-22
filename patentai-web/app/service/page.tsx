'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'
import { useState } from 'react'

export default function ServicePage() {
  const { lang } = useLang()
  const [active, setActive] = useState(0)
  const sp = t.svcPage

  const services = [
    {
      num: '01', href: '/service/consultation',
      tag: 'CONSULTATION',
      title:   tr(sp.s1title, lang),
      summary: tr(sp.s1summary, lang),
      desc:    tr(sp.s1desc, lang),
      steps:   [tr(sp.s1step1, lang), tr(sp.s1step2, lang), tr(sp.s1step3, lang), tr(sp.s1step4, lang)],
      output:  tr(sp.s1output, lang),
      time: '5–10분',
    },
    {
      num: '02', href: '/service/prior-art',
      tag: 'PRIOR ART',
      title:   tr(sp.s2title, lang),
      summary: tr(sp.s2summary, lang),
      desc:    tr(sp.s2desc, lang),
      steps:   [tr(sp.s2step1, lang), tr(sp.s2step2, lang), tr(sp.s2step3, lang), tr(sp.s2step4, lang)],
      output:  tr(sp.s2output, lang),
      time: '2–5분',
    },
    {
      num: '03', href: '/service/specification',
      tag: 'SPECIFICATION',
      title:   tr(sp.s3title, lang),
      summary: tr(sp.s3summary, lang),
      desc:    tr(sp.s3desc, lang),
      steps:   [tr(sp.s3step1, lang), tr(sp.s3step2, lang), tr(sp.s3step3, lang), tr(sp.s3step4, lang)],
      output:  tr(sp.s3output, lang),
      time: '3–7분',
    },
    {
      num: '04', href: '/service/drawing',
      tag: 'DRAWING AGENT',
      title:   tr(sp.s4title, lang),
      summary: tr(sp.s4summary, lang),
      desc:    tr(sp.s4desc, lang),
      steps:   [tr(sp.s4step1, lang), tr(sp.s4step2, lang), tr(sp.s4step3, lang), tr(sp.s4step4, lang)],
      output:  tr(sp.s4output, lang),
      time: '30초–2분',
    },
    {
      num: '05', href: '/service/review',
      tag: 'EMBODIMENT',
      title:   tr(sp.s5title, lang),
      summary: tr(sp.s5summary, lang),
      desc:    tr(sp.s5desc, lang),
      steps:   [tr(sp.s5step1, lang), tr(sp.s5step2, lang), tr(sp.s5step3, lang), tr(sp.s5step4, lang)],
      output:  tr(sp.s5output, lang),
      time: '2–3분',
    },
  ]

  const s = services[active]

  return (
    <div className="site">
      <style>{`
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
        <p>{tr(sp.heroDesc, lang)}</p>
      </div>

      <div className="pipeline-bar">
        {services.map((svc, i) => (
          <div key={svc.num} className={`pipeline-item ${active === i ? 'active' : ''}`} onClick={() => setActive(i)}>
            <div className="pi-num">{svc.num}</div>
            <div className="pi-label">{svc.title}</div>
          </div>
        ))}
      </div>

      <div className="svc-detail" style={{ background:'white' }}>
        <div className="svc-left">
          <div className="svc-tag">{s.tag}</div>
          <div className="svc-title">{s.title}</div>
          <div className="svc-summary">{s.summary}</div>
          <div className="svc-desc">{s.desc}</div>

          <div className="svc-section-label">{tr(sp.stepsLabel, lang)}</div>
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
            <div><div className="svc-meta-label">{tr(sp.timeLabel, lang)}</div><div className="svc-meta-value">{s.time}</div></div>
            <div><div className="svc-meta-label">{tr(sp.typeLabel, lang)}</div><div className="svc-meta-value">{s.tag}</div></div>
          </div>
        </div>

        <div className="svc-right">
          <div className="svc-section-label">{tr(sp.outputLabel, lang)}</div>
          <div className="svc-output-box">{s.output}</div>

          {s.num === '04' && (
            <>
              <div className="svc-section-label">{tr(sp.drawingSample, lang)}</div>
              <div className="img-preview">
                <img src="/drawings/sample_block.svg" alt="block diagram" />
              </div>
              <div className="img-preview">
                <img src="/drawings/sample_flow.svg" alt="flowchart" />
              </div>
            </>
          )}

          <div className="svc-actions">
            <Link href={s.href} className="svc-btn svc-btn-primary">{tr(sp.detailBtn, lang)}</Link>
            {s.num === '04' && <Link href="/gallery" className="svc-btn svc-btn-outline">{tr(sp.galleryBtn, lang)}</Link>}
            <Link href="/contact" className="svc-btn svc-btn-outline">{tr(sp.consultBtn, lang)}</Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
