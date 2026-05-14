import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const items = [
  { date: '2024.12', title: 'WIPO IPC 2025년판 개정', desc: 'AI·양자컴퓨팅·지속가능에너지 분야 신규 IPC 코드 대거 추가. 국내 출원 분류 체계도 연동 업데이트 예정.', url: 'https://ipcpub.wipo.int' },
  { date: '2024.10', title: 'CPC 분류 체계 업데이트', desc: 'EPO와 USPTO가 공동 운영하는 CPC 분류가 반도체·배터리·AI 하드웨어 분야를 중심으로 업데이트되었습니다.', url: 'https://www.cooperativepatentclassification.org' },
  { date: '2024.08', title: 'AI 기반 IPC 자동 분류 서비스 도입', desc: '특허청이 출원 시 IPC 분류를 AI로 자동 추천하는 서비스를 도입하여 출원인의 편의를 높였습니다.', url: 'https://www.kipo.go.kr' },
]

export default function Page() {
  return (
    <div className="site">
      <Nav />
      <div className="hero">
        <div className="tag">IPC / CPC CLASSIFICATION</div>
        <h1>IPC / CPC 분류</h1>
        <p>국제 특허 분류 체계의 최신 업데이트와 활용 방법을 안내합니다.</p>
      </div>
      <div className="section">
        <div className="line"></div>
        <div className="title">IPC / CPC 분류</div>
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
