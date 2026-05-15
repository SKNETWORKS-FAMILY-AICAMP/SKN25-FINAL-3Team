'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

const news = [
  { category: 'AI PATENT', date: '2025.04', title: 'AI 생성물 특허 출원 급증', desc: '특허청, 생성형 AI 관련 특허 출원이 전년 대비 42% 증가했다고 발표. 출원 자동화 도구 수요도 함께 확대.', img: 'https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=600&q=80', links: [{ label: '특허청 AI 특허 동향 보고서', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200172' }, { label: 'WIPO AI 특허 분석', url: 'https://www.wipo.int/tech_trends/en/artificial_intelligence/' }] },
  { category: 'PRIOR ART', date: '2025.03', title: 'KIPRIS 검색 고도화 업데이트', desc: '특허청 KIPRIS, 벡터 유사도 기반 선행기술 검색 기능 추가. 키워드 검색 대비 관련도 높은 결과 제공.', img: 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=600&q=80', links: [{ label: 'KIPRIS 특허 검색', url: 'https://www.kipris.or.kr' }, { label: 'Google Patents', url: 'https://patents.google.com' }] },
  { category: 'DRAWING',   date: '2025.03', title: '특허 도면 자동 생성 기술 상용화', desc: '명세서 텍스트만으로 블록도·흐름도를 자동 생성하는 AI 도면 에이전트가 특허 실무에 본격 도입.', img: 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80', links: [{ label: '특허청 도면 작성 가이드', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200060' }, { label: '특허로 온라인 출원', url: 'https://www.patent.go.kr' }] },
  { category: 'POLICY',    date: '2025.02', title: '2025 지식재산 기본계획 발표', desc: '특허청, AI·바이오·반도체 분야 우선심사 확대 및 심사 처리 기간 단축 계획 발표. 스타트업 지원 강화.', img: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=600&q=80', links: [{ label: '특허청 정책 발표', url: 'https://www.kipo.go.kr/ko/kpoContentView.do?menuCd=SCD0200045' }, { label: '지식재산 기본계획 전문', url: 'https://www.kipo.go.kr' }] },
  { category: 'CLAIMS',    date: '2025.01', title: 'LLM 기반 청구항 자동 작성 연구', desc: '국내 대학·연구기관이 발명 설명을 입력하면 독립항·종속항을 자동 구성하는 sLLM 모델을 공개.', img: 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&q=80', links: [{ label: '청구범위 작성 가이드 (KIPO)', url: 'https://www.kipo.go.kr' }, { label: 'USPTO 청구항 가이드', url: 'https://www.uspto.gov/patents/basics/patent-process-overview' }] },
  { category: 'IPC / CPC', date: '2024.12', title: 'WIPO IPC 2025년판 개정', desc: 'AI·양자컴퓨팅·지속가능에너지 분야 신규 IPC 코드 대거 추가. 국내 출원 분류 체계도 연동 업데이트 예정.', img: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&q=80', links: [{ label: 'IPC 분류표 (WIPO)', url: 'https://ipcpub.wipo.int' }, { label: 'CPC 분류 검색 (EPO)', url: 'https://www.cooperativepatentclassification.org' }] },
]

export default function NewsPage() {
  const { lang } = useLang()
  const nm = t.news

  return (
    <div className="site">
      <style>{`
        .news-card { background: white; border: 1px solid #E8E4DC; box-shadow: 0 12px 30px rgba(0,0,0,.04); transition: .2s; display: flex; flex-direction: column; overflow: hidden; }
        .news-card:hover { transform: translateY(-5px); box-shadow: 0 18px 38px rgba(0,0,0,.09); }
        .news-thumb { width: 100%; height: 190px; object-fit: cover; display: block; filter: brightness(0.88) saturate(0.9); transition: filter 0.2s; }
        .news-card:hover .news-thumb { filter: brightness(1) saturate(1); }
        .news-body { padding: 1.6rem 2rem 2rem; display: flex; flex-direction: column; flex: 1; }
        .news-date { color: #999; font-size: 0.78rem; margin-bottom: 0.3rem; }
        .news-links { margin-top: auto; padding-top: 1.2rem; border-top: 1px solid #EEE; display: flex; flex-direction: column; gap: 0.5rem; }
        .news-link { color: #C9A84C; font-size: 0.82rem; font-weight: 600; text-decoration: none; display: flex; align-items: center; gap: 0.4rem; transition: color 0.15s; }
        .news-link:hover { color: #111128; }
        .news-link::before { content: '→'; font-size: 0.75rem; }
      `}</style>
      <Nav />
      <div className="hero">
        <div className="tag">{tr(nm.tag, lang)}</div>
        <h1>{tr(nm.h1, lang)}</h1>
        <p>{tr(nm.desc, lang)}</p>
      </div>
      <div className="section">
        <style>{`
          .nc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.4rem; }
          .nc { background: white; border: 1px solid #E8E4DC; overflow: hidden; display: flex; flex-direction: column; transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s, border-color .25s; }
          .nc:hover { transform: translateY(-5px); box-shadow: 0 16px 40px rgba(0,0,0,.09); border-color: rgba(201,168,76,.35); }
          .nc-img { width: 100%; height: 175px; object-fit: cover; display: block; filter: brightness(.85) saturate(.85); transition: filter .3s; }
          .nc:hover .nc-img { filter: brightness(1) saturate(1); }
          .nc-body { padding: 1.5rem 1.6rem 1.8rem; display: flex; flex-direction: column; flex: 1; }
          .nc-top { display: flex; align-items: center; gap: .6rem; margin-bottom: .8rem; }
          .nc-cat { background: #08081A; color: #C9A84C; font-size: .58rem; font-weight: 700; letter-spacing: .12em; padding: 2px 8px; }
          .nc-date { color: #BBB; font-size: .74rem; }
          .nc-title { font-size: .97rem; font-weight: 700; color: #111128; line-height: 1.45; margin-bottom: .6rem; }
          .nc-desc { font-size: .83rem; color: #666; line-height: 1.78; word-break: keep-all; flex: 1; }
          .nc-links { margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid #F0EDE8; display: flex; flex-direction: column; gap: .4rem; }
          .nc-link { color: #C9A84C; font-size: .78rem; font-weight: 600; text-decoration: none; display: flex; align-items: center; gap: .3rem; transition: color .15s; }
          .nc-link:hover { color: #111128; }
          @media(max-width:900px){ .nc-grid { grid-template-columns: 1fr 1fr; } }
          @media(max-width:540px){ .nc-grid { grid-template-columns: 1fr; } }
        `}</style>
        <div className="line"></div>
        <div className="title">{tr(nm.title, lang)}</div>
        <div className="sub">{tr(nm.sub, lang)}</div>
        <div className="nc-grid">
          {news.map((item, i) => (
            <div className="nc" key={i}>
              <img className="nc-img" src={item.img} alt={item.title} />
              <div className="nc-body">
                <div className="nc-top">
                  <span className="nc-cat">{item.category}</span>
                  <span className="nc-date">{item.date}</span>
                </div>
                <div className="nc-title">{item.title}</div>
                <div className="nc-desc">{item.desc}</div>
                <div className="nc-links">
                  {item.links.map(link => (
                    <a key={link.url} className="nc-link" href={link.url} target="_blank" rel="noopener noreferrer">
                      → {link.label}
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
