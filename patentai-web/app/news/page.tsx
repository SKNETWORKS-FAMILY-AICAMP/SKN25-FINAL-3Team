import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

const items = [
  { num: '01', category: 'AI PATENT', title: 'AI 특허 자동화 확대', desc: '생성형 AI를 활용한 특허 상담, 분석, 명세서 작성 자동화가 확대되고 있습니다.' },
  { num: '02', category: 'PRIOR ART', title: '선행기술 조사 고도화', desc: '대규모 특허 데이터를 기반으로 유사 기술과 신규성 위험을 빠르게 검토합니다.' },
  { num: '03', category: 'DRAWING', title: '도면 자동 생성 기술', desc: '명세서의 구성요소와 처리 흐름을 분석해 특허 도면을 자동 구성합니다.' },
  { num: '04', category: 'REVIEW', title: '심사 대응 자동화', desc: '거절이유를 분석하고 의견서와 보정 방향을 AI가 제안합니다.' },
  { num: '05', category: 'CLAIMS', title: '청구항 구조 분석', desc: '독립항과 종속항의 관계를 파악하고 권리범위를 구조화합니다.' },
  { num: '06', category: 'IPC / CPC', title: 'IPC 분류 추천', desc: '기술 내용을 분석하여 적합한 IPC/CPC 분류를 추천합니다.' },
]

export default function NewsPage() {
  return (
    <div className="site">
      <Nav />

      <div className="hero">
        <div className="tag">NEWS &amp; INSIGHTS</div>
        <h1>소식 / 자료</h1>
        <p>AI 특허 자동화, 선행기술 조사, 명세서 작성 관련 주요 자료를 제공합니다.</p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">PatentAI 카드뉴스</div>
        <div className="sub">최근 주요 특허 이슈와 AI 기술 동향을 확인하세요.</div>

        <div className="grid">
          {items.map((item) => (
            <div className="news-card" key={item.num}>
              <div className="thumb">{item.num}</div>
              <div className="category">{item.category}</div>
              <h3>{item.title}</h3>
              <p>{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  )
}
