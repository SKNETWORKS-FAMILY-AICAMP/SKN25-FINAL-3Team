'use client'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const positions = [
  { dept:'AI 연구', title:'특허 AI 모델 엔지니어', type:'정규직', loc:'서울', desc:'특허 명세서 생성 sLLM 파인튜닝 및 RAG 파이프라인 고도화를 담당합니다.' },
  { dept:'엔지니어링', title:'백엔드 개발자 (Python/Django)', type:'정규직', loc:'서울', desc:'특허 상담 API 및 Supabase DB 연동 백엔드 시스템을 개발합니다.' },
  { dept:'엔지니어링', title:'프론트엔드 개발자 (Next.js)', type:'정규직', loc:'서울', desc:'PatentAI 웹서비스 UI/UX 개발 및 사용자 경험 개선을 담당합니다.' },
  { dept:'특허 전문', title:'변리사 (AI 특허 전문)', type:'정규직', loc:'서울', desc:'AI 발명 특허 출원 검토, AI 모델 출력물 품질 관리를 담당합니다.' },
  { dept:'데이터', title:'특허 데이터 분석가', type:'계약직', loc:'서울/원격', desc:'특허 공보 데이터 수집·정제 및 AI 학습 데이터셋 구축을 담당합니다.' },
]

const values = [
  { title:'탁월함', desc:'우리는 매 서비스에서 특허 전문가 수준의 품질을 추구합니다.' },
  { title:'혁신', desc:'AI 기술의 최전선에서 특허 실무를 재정의합니다.' },
  { title:'신뢰', desc:'발명자의 아이디어를 가장 안전하게 보호합니다.' },
]

export default function CareersPage() {
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
        <div className="tag">CAREERS</div>
        <h1>인재채용</h1>
        <p>PatentAI와 함께 지식재산의 미래를 만들어갈 인재를 찾습니다.</p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">우리가 추구하는 가치</div>
        <div className="sub">PatentAI의 구성원은 탁월함·혁신·신뢰를 바탕으로 일합니다.</div>
        <div className="careers-grid">
          {values.map(v => (
            <div key={v.title} className="careers-value">
              <div className="careers-value-title">{v.title}</div>
              <div className="careers-value-desc">{v.desc}</div>
            </div>
          ))}
        </div>

        <div className="line"></div>
        <div className="title">채용 공고</div>
        <div className="sub">현재 모집 중인 포지션입니다.</div>

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
                <Link className="job-apply" href="/contact">지원하기 →</Link>
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop:'3rem', background:'#08081A', padding:'3rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'1rem' }}>
          <div>
            <div style={{ color:'#C9A84C', fontSize:'.7rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'.5rem' }}>OPEN APPLICATION</div>
            <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.4rem', fontWeight:300, color:'#F0EDE6', marginBottom:'.3rem' }}>원하는 포지션이 없으신가요?</div>
            <div style={{ color:'#666688', fontSize:'.86rem' }}>언제든지 자유 지원이 가능합니다.</div>
          </div>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2.2rem', border:'1px solid #C9A84C', color:'#C9A84C', fontSize:'.82rem', fontWeight:700, letterSpacing:'.08em', whiteSpace:'nowrap' }}>
            자유 지원하기 →
          </Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
