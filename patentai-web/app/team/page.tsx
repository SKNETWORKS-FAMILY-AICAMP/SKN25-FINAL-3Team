'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

const members = [
  { num: '01', name: '권가영',  role: 'Prior Art Agent',            desc: '선행기술 조사, 특허 데이터 검색, 유사도 분석 기능을 담당합니다.', slug: 'gayeongkwon' },
  { num: '02', name: '김서현',  role: 'Frontend / PatentAI UI',     desc: '홈페이지 UI, Next.js 화면 구성, 도면 에이전트 연동을 담당합니다.', slug: 'seohyunkim' },
  { num: '03', name: '김홍익',  role: 'Consultation Agent',         desc: '발명 상담 흐름, 상담 로그 구조화, 발명 요약 기능을 담당합니다.', slug: 'hongikkim' },
  { num: '04', name: '박범수',  role: 'Specification / Claims',     desc: '청구항, 명세서 초안, 발명의 효과 및 구성요소 정리 기능을 담당합니다.', slug: 'beomsoopark' },
  { num: '05', name: '조은석',  role: 'Drawing Agent',              desc: '특허 도면 자동 생성, SVG/PNG 렌더링, 품질 검증 기능을 담당합니다.', slug: 'eunseokjo' },
  { num: '06', name: '최현우',  role: 'Review / Integration',       desc: '검토 에이전트, 전체 서비스 통합, 배포 및 발표 자료 정리를 담당합니다.', slug: 'hyeonwoochoi' },
]

export default function TeamPage() {
  const { lang } = useLang()
  const tm = t.team

  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">{tr(tm.tag, lang)}</div>
        <h1>{tr(tm.h1, lang)}</h1>
        <p>{tr(tm.desc, lang)}</p>
      </div>
      <div className="section">
        <div className="line"></div>
        <div className="title">{tr(tm.title, lang)}</div>
        <div className="sub">{tr(tm.sub, lang)}</div>
        <div className="grid">
          {members.map((m) => {
            const card = (
              <div className="member" key={m.num} style={m.slug ? { cursor: 'pointer' } : {}}>
                <div className="avatar">{m.num}</div>
                <div className="name">{m.name}</div>
                <div className="role">{m.role}</div>
                <div className="desc">{m.desc}</div>
                {m.slug && <div style={{ marginTop: '1rem', color: '#C9A84C', fontSize: '0.82rem', fontWeight: 600 }}>{tr(tm.profile, lang)}</div>}
              </div>
            )
            return m.slug
              ? <Link href={`/team/${m.slug}`} key={m.num} style={{ textDecoration: 'none' }}>{card}</Link>
              : card
          })}
        </div>
      </div>
      <Footer />
    </div>
  )
}
