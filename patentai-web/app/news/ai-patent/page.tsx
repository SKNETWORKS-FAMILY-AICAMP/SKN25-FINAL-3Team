'use client'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const items = [
  { date: '2025.04', title: 'AI 생성물 특허 출원 급증', desc: '특허청, 생성형 AI 관련 특허 출원이 전년 대비 42% 증가했다고 발표. 출원 자동화 도구 수요도 함께 확대.', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200172' },
  { date: '2025.02', title: 'WIPO AI 특허 동향 보고서 2025', desc: 'WIPO가 발표한 AI 특허 현황 보고서에 따르면 한국은 AI 특허 출원 세계 4위를 기록했습니다.', url: 'https://www.wipo.int/tech_trends/en/artificial_intelligence/' },
  { date: '2025.01', title: 'LLM 기반 특허 명세서 자동화 연구', desc: '국내 연구기관이 GPT 기반 특허 명세서 자동 작성 시스템의 성능을 검증한 논문을 발표했습니다.', url: 'https://arxiv.org/search/?searchtype=all&query=patent+LLM+specification' },
  { date: '2024.12', title: 'AI 발명자 인정 논쟁 본격화', desc: '미국·유럽 특허청이 AI를 발명자로 인정할 수 없다고 결정한 가운데, 국내 특허청의 입장이 주목받고 있습니다.', url: 'https://www.epo.org/en/news-events/in-focus/espace/artificial-intelligence' },
]

export default function Page() {
  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">AI PATENT TRENDS</div>
        <h1>AI 특허 동향</h1>
        <p>생성형 AI와 특허 자동화 관련 최신 동향을 제공합니다.</p>
      </div>
      <div className="section">
        <div className="line"></div>
        <div className="title">AI 특허 동향</div>
        <Link href="/news" style={{ color:'#C9A84C', fontSize:'.82rem', textDecoration:'none', display:'inline-block', marginBottom:'2rem' }}>← 전체 소식 보기</Link>
        <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
          {items.map((item, i) => (
            <a key={i} href={item.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration:'none' }}>
              <div style={{ background:'white', border:'1px solid #E8E4DC', padding:'1.8rem 2rem', transition:'.2s', cursor:'pointer' }}
                onMouseEnter={e => (e.currentTarget.style.borderColor='rgba(201,168,76,.5)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor='#E8E4DC')}>
                <div style={{ color:'#999', fontSize:'.76rem', marginBottom:'.4rem' }}>{item.date}</div>
                <div style={{ color:'#111128', fontWeight:700, fontSize:'1rem', marginBottom:'.5rem' }}>{item.title}</div>
                <div style={{ color:'#666', fontSize:'.88rem', lineHeight:1.75 }}>{item.desc}</div>
              </div>
            </a>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  )
}
