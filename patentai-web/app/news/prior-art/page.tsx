import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const items = [
  { date: '2025.03', title: 'KIPRIS 벡터 검색 기능 업데이트', desc: '특허청 KIPRIS, 벡터 유사도 기반 선행기술 검색 기능 추가. 키워드 검색 대비 관련도 높은 결과 제공.', url: 'https://www.kipris.or.kr' },
  { date: '2025.01', title: 'Google Patents AI 검색 고도화', desc: 'Google Patents가 자연어 검색 기능을 강화하여 발명 내용만으로 유사 특허를 탐색할 수 있게 되었습니다.', url: 'https://patents.google.com' },
  { date: '2024.11', title: 'EPO Espacenet 새 인터페이스 출시', desc: 'EPO가 Espacenet 검색 인터페이스를 개편하여 CPC 분류 기반 고급 검색 기능을 강화했습니다.', url: 'https://worldwide.espacenet.com' },
]

export default function Page() {
  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">PRIOR ART RESOURCES</div>
        <h1>선행기술 자료</h1>
        <p>특허 선행기술 조사에 활용할 수 있는 최신 자료와 도구를 제공합니다.</p>
      </div>
      <div className="section">
        <div className="line"></div>
        <div className="title">선행기술 자료</div>
        <Link href="/news" style={{ color:'#C9A84C', fontSize:'.82rem', textDecoration:'none', display:'inline-block', marginBottom:'2rem' }}>← 전체 소식 보기</Link>
        <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
          {items.map((item, i) => (
            <a key={i} href={item.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration:'none' }}>
              <div style={{ background:'white', border:'1px solid #E8E4DC', padding:'1.8rem 2rem', transition:'.2s' }}
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
