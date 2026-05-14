import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

const items = [
  {
    num: '01',
    category: 'AI PATENT',
    title: 'AI 특허 자동화 확대',
    desc: '생성형 AI를 활용한 특허 상담, 분석, 명세서 작성 자동화가 확대되고 있습니다.',
    img: 'https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=600&q=80',
    imgAlt: 'AI 칩 이미지',
    links: [
      { label: '특허청 AI 특허 동향 보고서', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200172' },
      { label: 'WIPO AI 특허 분석', url: 'https://www.wipo.int/tech_trends/en/artificial_intelligence/' },
    ],
  },
  {
    num: '02',
    category: 'PRIOR ART',
    title: '선행기술 조사 고도화',
    desc: '대규모 특허 데이터를 기반으로 유사 기술과 신규성 위험을 빠르게 검토합니다.',
    img: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=600&q=80',
    imgAlt: '도서관 자료 조사',
    links: [
      { label: 'KIPRIS 특허 검색', url: 'https://www.kipris.or.kr' },
      { label: 'Google Patents', url: 'https://patents.google.com' },
    ],
  },
  {
    num: '03',
    category: 'DRAWING',
    title: '도면 자동 생성 기술',
    desc: '명세서의 구성요소와 처리 흐름을 분석해 특허 도면을 자동 구성합니다.',
    img: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80',
    imgAlt: '기술 블루프린트 도면',
    links: [
      { label: '특허청 도면 작성 가이드', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200060' },
      { label: '특허 도면 규정 (특허청)', url: 'https://www.kipo.go.kr' },
    ],
  },
  {
    num: '04',
    category: 'REVIEW',
    title: '심사 대응 자동화',
    desc: '거절이유를 분석하고 의견서와 보정 방향을 AI가 제안합니다.',
    img: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&q=80',
    imgAlt: '계약서 서명',
    links: [
      { label: '특허 심사 기준 (특허청)', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200045' },
      { label: '특허로 온라인 출원', url: 'https://www.patent.go.kr' },
    ],
  },
  {
    num: '05',
    category: 'CLAIMS',
    title: '청구항 구조 분석',
    desc: '독립항과 종속항의 관계를 파악하고 권리범위를 구조화합니다.',
    img: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&q=80',
    imgAlt: '법률 문서 작성',
    links: [
      { label: '청구범위 작성 가이드 (KIPO)', url: 'https://www.kipo.go.kr' },
      { label: 'USPTO 청구항 가이드', url: 'https://www.uspto.gov/patents/basics/patent-process-overview' },
    ],
  },
  {
    num: '06',
    category: 'IPC / CPC',
    title: 'IPC 분류 추천',
    desc: '기술 내용을 분석하여 적합한 IPC/CPC 분류를 추천합니다.',
    img: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&q=80',
    imgAlt: '데이터 분석 차트',
    links: [
      { label: 'IPC 분류표 (WIPO)', url: 'https://ipcpub.wipo.int' },
      { label: 'CPC 분류 검색 (EPO)', url: 'https://www.cooperativepatentclassification.org' },
    ],
  },
]

export default function NewsPage() {
  return (
    <div className="site">
      <style>{`
        .news-card {
          background: white;
          border: 1px solid #E8E4DC;
          min-height: 250px;
          box-shadow: 0 12px 30px rgba(0,0,0,.04);
          transition: .2s;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .news-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 18px 38px rgba(0,0,0,.09);
        }
        .news-thumb {
          width: 100%;
          height: 190px;
          object-fit: cover;
          display: block;
          filter: brightness(0.88) saturate(0.9);
          transition: filter 0.2s;
        }
        .news-card:hover .news-thumb {
          filter: brightness(1) saturate(1);
        }
        .news-body {
          padding: 1.6rem 2rem 2rem;
          display: flex;
          flex-direction: column;
          flex: 1;
        }
        .news-links {
          margin-top: auto;
          padding-top: 1.2rem;
          border-top: 1px solid #EEE;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .news-link {
          color: #C9A84C;
          font-size: 0.82rem;
          font-weight: 600;
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          transition: color 0.15s;
        }
        .news-link:hover { color: #111128; }
        .news-link::before { content: '→'; font-size: 0.75rem; }
      `}</style>

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
              <img className="news-thumb" src={item.img} alt={item.imgAlt} />
              <div className="news-body">
                <div className="category">{item.category}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
                <div className="news-links">
                  {item.links.map((link) => (
                    <a
                      key={link.url}
                      className="news-link"
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  )
}
