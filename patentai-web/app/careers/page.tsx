'use client'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function CareersPage() {
  const { lang } = useLang()
  const c = t.careers

  const positions = [
    { dept:'AI Research',    title:'Patent AI Model Engineer',           type: lang==='ko'?'정규직':'Full-time', loc:'Seoul', desc: lang==='ko'?'특허 명세서 생성 sLLM 파인튜닝 및 RAG 파이프라인 고도화를 담당합니다.':'Fine-tuning sLLM for patent specification generation and RAG pipeline optimization.' },
    { dept:'Engineering',    title:'Backend Developer (Python/Django)',   type: lang==='ko'?'정규직':'Full-time', loc:'Seoul', desc: lang==='ko'?'특허 상담 API 및 Supabase DB 연동 백엔드 시스템을 개발합니다.':'Building patent consultation API and Supabase DB integration backend.' },
    { dept:'Engineering',    title:'Frontend Developer (Next.js)',        type: lang==='ko'?'정규직':'Full-time', loc:'Seoul', desc: lang==='ko'?'PatentAI 웹서비스 UI/UX 개발 및 사용자 경험 개선을 담당합니다.':'Developing PatentAI web service UI/UX and improving user experience.' },
    { dept:'Patent Expert',  title:'Patent Attorney (AI Specialist)',     type: lang==='ko'?'정규직':'Full-time', loc:'Seoul', desc: lang==='ko'?'AI 발명 특허 출원 검토, AI 모델 출력물 품질 관리를 담당합니다.':'Reviewing AI invention patent applications and managing AI model output quality.' },
    { dept:'Data',           title:'Patent Data Analyst',                type: lang==='ko'?'계약직':'Contract', loc: lang==='ko'?'서울/원격':'Seoul/Remote', desc: lang==='ko'?'특허 공보 데이터 수집·정제 및 AI 학습 데이터셋 구축을 담당합니다.':'Collecting and refining patent data and building AI training datasets.' },
  ]

  const values = [
    { title: tr(c.v1t, lang), desc: tr(c.v1d, lang) },
    { title: tr(c.v2t, lang), desc: tr(c.v2d, lang) },
    { title: tr(c.v3t, lang), desc: tr(c.v3d, lang) },
  ]

  return (
    <div className="site">
      <style>{`
        .careers-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:1px; background:#E0DDD8; margin-bottom:4rem; }
        .careers-value { background:white; padding:2rem; }
        .careers-value-title { font-family:'Noto Serif KR',serif; font-size:1.1rem; font-weight:300; color:#0A0A16; margin-bottom:.6rem; }
        .careers-value-desc { font-size:.87rem; color:#666; line-height:1.85; }
        .job-item { background:white; border-bottom:1px solid #E8E4DC; padding:2rem; display:flex; align-items:flex-start; justify-content:space-between; gap:2rem; transition:.15s; }
        .job-item:hover { background:#FAFAF8; }
        .job-dept { font-size:.68rem; font-weight:700; color:#C9A84C; letter-spacing:.15em; text-transform:uppercase; margin-bottom:.4rem; }
        .job-title { font-size:1rem; font-weight:700; color:#0A0A16; margin-bottom:.4rem; }
        .job-desc { font-size:.85rem; color:#666; line-height:1.7; }
        .job-meta { display:flex; flex-direction:column; align-items:flex-end; gap:.4rem; flex-shrink:0; }
        .job-tag { font-size:.7rem; border:1px solid #E8E4DC; color:#888; padding:3px 10px; white-space:nowrap; }
        .job-apply { font-size:.72rem; color:#C9A84C; font-weight:700; letter-spacing:.08em; margin-top:.5rem; text-decoration:none; }
        .job-apply:hover { text-decoration:underline; }
        @media(max-width:900px){ .careers-grid { grid-template-columns:1fr; } .job-item { flex-direction:column; } }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">{tr(c.tag, lang)}</div>
        <h1>{tr(c.h1, lang)}</h1>
        <p>{tr(c.desc, lang)}</p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">{tr(c.valTitle, lang)}</div>
        <div className="sub">{tr(c.valSub, lang)}</div>
        <div className="careers-grid">
          {values.map(v => (
            <div key={v.title} className="careers-value">
              <div className="careers-value-title">{v.title}</div>
              <div className="careers-value-desc">{v.desc}</div>
            </div>
          ))}
        </div>

        <div className="line"></div>
        <div className="title">{tr(c.jobTitle, lang)}</div>
        <div className="sub">{tr(c.jobSub, lang)}</div>

        <div style={{ border:'1px solid #E8E4DC' }}>
          {positions.map((p, i) => (
            <div key={i} className="job-item">
              <div>
                <div className="job-dept">{p.dept}</div>
                <div className="job-title">{p.title}</div>
                <div className="job-desc">{p.desc}</div>
              </div>
              <div className="job-meta">
                <span className="job-tag">{p.type}</span>
                <span className="job-tag">{p.loc}</span>
                <Link className="job-apply" href="/contact">{tr(c.apply, lang)}</Link>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop:'3rem', background:'#08081A', padding:'3rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'1rem' }}>
          <div>
            <div style={{ color:'#C9A84C', fontSize:'.7rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'.5rem' }}>{tr(c.openTag, lang)}</div>
            <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.4rem', fontWeight:300, color:'#F0EDE6', marginBottom:'.3rem' }}>{tr(c.openTitle, lang)}</div>
            <div style={{ color:'#666688', fontSize:'.86rem' }}>{tr(c.openSub, lang)}</div>
          </div>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2.2rem', border:'1px solid #C9A84C', color:'#C9A84C', fontSize:'.82rem', fontWeight:700, letterSpacing:'.08em', whiteSpace:'nowrap' }}>
            {tr(c.openBtn, lang)}
          </Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
