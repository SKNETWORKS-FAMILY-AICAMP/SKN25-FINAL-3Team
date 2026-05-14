import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const items = [
  { date: '2025.02', title: '2025 지식재산 기본계획 발표', desc: '특허청, AI·바이오·반도체 분야 우선심사 확대 및 심사 처리 기간 단축 계획 발표. 스타트업 지원 강화.', url: 'https://www.kipo.go.kr' },
  { date: '2025.01', title: '특허 심사 처리기간 단축 방침', desc: '특허청이 2025년 평균 심사 처리기간을 14개월로 단축하겠다는 목표를 발표했습니다.', url: 'https://www.kipo.go.kr' },
  { date: '2024.12', title: '중소기업 우선심사 대상 확대', desc: '특허청이 우선심사 신청 자격 요건을 완화하여 더 많은 중소·벤처기업이 혜택을 받을 수 있게 됩니다.', url: 'https://www.kipo.go.kr' },
]

export default function Page() {
  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">KIPO POLICY</div>
        <h1>특허청 정책</h1>
        <p>특허청 정책 변경과 제도 개선 사항을 안내합니다.</p>
      </div>
      <div className="section">
        <div className="line"></div>
        <div className="title">특허청 정책</div>
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
