'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function TeamPage() {
  const { lang } = useLang()
  const tm = t.team

  const members = [
    { num: '01', name: '권가영',  role: 'Prior Art Agent',            desc: tr(tm.m1desc, lang), slug: 'gayeongkwon' },
    { num: '02', name: '김서현',  role: 'Frontend / PatentAI UI',     desc: tr(tm.m2desc, lang), slug: 'seohyunkim' },
    { num: '03', name: '김홍익',  role: 'Consultation Agent',         desc: tr(tm.m3desc, lang), slug: 'hongikkim' },
    { num: '04', name: '박범수',  role: 'Specification / Claims',     desc: tr(tm.m4desc, lang), slug: 'beomsoopark' },
    { num: '05', name: '조은석',  role: 'Drawing Agent',              desc: tr(tm.m5desc, lang), slug: 'eunseokjo' },
    { num: '06', name: '최현우',  role: 'Review / Integration',       desc: tr(tm.m6desc, lang), slug: 'hyeonwoochoi' },
  ]

  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">{tr(tm.tag, lang)}</div>
        <h1>{tr(tm.h1, lang)}</h1>
        <p>{tr(tm.desc, lang)}</p>
      </div>
      <div className="section" style={{ paddingBottom: 0, background: 'white' }}>
        <div className="line"></div>
        <div className="title">{tr(tm.title, lang)}</div>
        <div className="sub">{tr(tm.sub, lang)}</div>
        <div className="grid" style={{ background: '#E8E4DC' }}>
          {members.map((m) => {
            const card = (
              <div className="member" key={m.num} style={{ cursor: 'pointer', minHeight: 0, background: 'white', height: '100%', boxSizing: 'border-box' }}>
                <div className="avatar">{m.num}</div>
                <div className="name">{m.name}</div>
                <div className="role">{m.role}</div>
                <div className="desc" style={{ wordBreak: 'keep-all', overflowWrap: 'break-word', lineHeight: 1.85 }}>{m.desc}</div>
                {m.slug && <div style={{ marginTop: '1rem', color: '#C9A84C', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '.06em' }}>{tr(tm.profile, lang)}</div>}
              </div>
            )
            return m.slug
              ? <Link href={`/team/${m.slug}`} key={m.num} style={{ textDecoration: 'none', display: 'block', height: '100%' }}>{card}</Link>
              : card
          })}
        </div>
      </div>
      <Footer />
    </div>
  )
}
