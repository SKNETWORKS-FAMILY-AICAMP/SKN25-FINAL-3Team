'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const drawings = [
  {
    id: 'sample_block',
    file: '/drawings/sample_block.svg',
    title: '이미지 분류 시스템',
    type: 'block_diagram',
    typeLabel: 'BLOCK DIAGRAM',
    desc: '딥러닝 기반 이미지 분류 시스템의 전체 구성도. 입력부·전처리부·CNN 모델부·저장부·출력부 구조.',
    grade: 'A',
    score: 100,
  },
  {
    id: 'sample_flow',
    file: '/drawings/sample_flow.svg',
    title: '이미지 분류 처리 흐름도',
    type: 'flowchart',
    typeLabel: 'FLOWCHART',
    desc: '이미지 분류 방법의 단계별 처리 흐름. 유효성 판단 분기·오류 반환·분류 결과 출력 포함.',
    grade: 'A',
    score: 95,
  },
  {
    id: 'patent_block',
    file: '/drawings/patent_block.svg',
    title: '문장 제공 장치 구성도',
    type: 'block_diagram',
    typeLabel: 'BLOCK DIAGRAM',
    desc: '사용자 입력에 기반한 문장 제공 장치의 시스템 블록도. 실제 특허(10-2017-0144234) 기반.',
    grade: 'A',
    score: 90,
  },
  {
    id: 'patent_flow',
    file: '/drawings/patent_flow.svg',
    title: '문장 제공 방법 흐름도',
    type: 'flowchart',
    typeLabel: 'FLOWCHART',
    desc: '사용자 입력 기반 문장 제공 방법의 처리 순서도. 실제 특허(10-2017-0144234) 기반.',
    grade: 'B',
    score: 85,
  },
  {
    id: 'ai_block',
    file: '/drawings/ai_block.svg',
    title: 'AI 시스템 구성도',
    type: 'block_diagram',
    typeLabel: 'BLOCK DIAGRAM',
    desc: 'AI 기반 시스템의 전체 구성 블록도. 데이터 파이프라인과 모듈 간 연관관계 표현.',
    grade: 'A',
    score: 100,
  },
  {
    id: 'ai_flow',
    file: '/drawings/ai_flow.svg',
    title: 'AI 처리 흐름도',
    type: 'flowchart',
    typeLabel: 'FLOWCHART',
    desc: 'AI 시스템의 데이터 처리 흐름. 판단 분기·반복 루프·출력 단계 포함.',
    grade: 'A',
    score: 100,
  },
  {
    id: 'rag_block',
    file: '/drawings/rag_block.svg',
    title: 'RAG 시스템 구성도',
    type: 'block_diagram',
    typeLabel: 'BLOCK DIAGRAM',
    desc: 'RAG(검색 증강 생성) 기반 시스템의 전체 구성 블록도. 벡터 DB·LLM·검색 파이프라인 구조.',
    grade: 'A',
    score: 100,
  },
  {
    id: 'rag_flow',
    file: '/drawings/rag_flow.svg',
    title: 'RAG 처리 흐름도',
    type: 'flowchart',
    typeLabel: 'FLOWCHART',
    desc: 'RAG 시스템의 질의 처리 흐름. 임베딩·검색·생성·응답 단계 순서도.',
    grade: 'A',
    score: 100,
  },
]

const typeFilters = [
  { id: 'all', label: '전체' },
  { id: 'block_diagram', label: '블록도' },
  { id: 'flowchart', label: '흐름도' },
]

export default function GalleryPage() {
  const [filter, setFilter] = useState('all')
  const [selected, setSelected] = useState<typeof drawings[0] | null>(null)

  const filtered = filter === 'all' ? drawings : drawings.filter(d => d.type === filter)

  return (
    <div className="site">
      <style>{`
        .gallery-filter { display:flex; gap:.5rem; margin-bottom:2.5rem; }
        .gallery-filter-btn {
          padding:.45rem 1.2rem; border:1px solid #E8E4DC;
          background:white; color:#666; font-size:.78rem; font-weight:600;
          cursor:pointer; letter-spacing:.06em; transition:.15s; font-family:inherit;
        }
        .gallery-filter-btn:hover { border-color:#C9A84C; color:#C9A84C; }
        .gallery-filter-btn.active { background:#111128; border-color:#111128; color:#C9A84C; }

        .gallery-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#E0DDD8; }
        .gallery-card { background:white; cursor:pointer; transition:background .15s; overflow:hidden; }
        .gallery-card:hover { background:#FAFAF8; }
        .gallery-card:hover .gallery-svg-wrap { opacity:.95; }

        .gallery-svg-wrap {
          width:100%; aspect-ratio:4/3; overflow:hidden;
          background:#FEFEFE; border-bottom:1px solid #F0EDE8;
          display:flex; align-items:center; justify-content:center;
          transition:opacity .15s;
        }
        .gallery-svg-wrap img { width:100%; height:100%; object-fit:contain; padding:.5rem; }
        .gallery-card-body { padding:1.4rem 1.6rem; }
        .gallery-type { color:#C9A84C; font-size:.65rem; font-weight:700; letter-spacing:.2em; margin-bottom:.4rem; }
        .gallery-title { font-weight:700; color:#0A0A16; font-size:.9rem; margin-bottom:.4rem; }
        .gallery-desc { font-size:.8rem; color:#666; line-height:1.7; margin-bottom:.8rem; }
        .gallery-meta { display:flex; align-items:center; justify-content:space-between; }
        .gallery-grade {
          font-size:.68rem; font-weight:700; letter-spacing:.1em;
          padding:2px 8px; border:1px solid;
        }
        .grade-A { border-color:rgba(39,174,96,.3); color:#27ae60; background:rgba(39,174,96,.05); }
        .grade-B { border-color:rgba(243,156,18,.3); color:#f39c12; background:rgba(243,156,18,.05); }
        .gallery-score { font-size:.75rem; color:#999; }

        /* 모달 */
        .gallery-modal-bg {
          position:fixed; inset:0; background:rgba(0,0,0,.75);
          z-index:9999; display:flex; align-items:center; justify-content:center;
          padding:2rem; animation:fadeIn .2s ease;
        }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        .gallery-modal {
          background:white; max-width:1000px; width:100%; max-height:90vh;
          display:flex; flex-direction:column; overflow:hidden;
        }
        .gallery-modal-header {
          padding:1.2rem 1.6rem; border-bottom:1px solid #E8E4DC;
          display:flex; align-items:center; justify-content:space-between;
          flex-shrink:0;
        }
        .gallery-modal-title { font-weight:700; color:#0A0A16; font-size:1rem; }
        .gallery-modal-close {
          background:none; border:none; font-size:1.4rem; cursor:pointer;
          color:#999; transition:color .15s; line-height:1; padding:0;
        }
        .gallery-modal-close:hover { color:#C9A84C; }
        .gallery-modal-body { flex:1; overflow:auto; padding:1.5rem; }
        .gallery-modal-body img { width:100%; height:auto; }
        .gallery-modal-footer {
          padding:1rem 1.6rem; border-top:1px solid #E8E4DC;
          display:flex; gap:.8rem; flex-shrink:0;
        }
        .gallery-dl-btn {
          padding:.6rem 1.4rem; border:1px solid #111128;
          background:#111128; color:#C9A84C; font-size:.78rem;
          font-weight:700; cursor:pointer; text-decoration:none;
          letter-spacing:.06em; transition:.15s; display:inline-block;
        }
        .gallery-dl-btn:hover { background:#C9A84C; color:#111128; border-color:#C9A84C; }
        .gallery-dl-btn.outline { background:white; color:#111128; border-color:#E8E4DC; }
        .gallery-dl-btn.outline:hover { border-color:#C9A84C; color:#C9A84C; }

        @media(max-width:900px){ .gallery-grid { grid-template-columns:1fr 1fr; } }
        @media(max-width:480px){ .gallery-grid { grid-template-columns:1fr; } }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">DRAWING GALLERY</div>
        <h1>특허 도면 갤러리</h1>
        <p>PatentAI가 자동 생성한 실제 특허 도면 샘플입니다.<br />특허청 실무 수준의 SVG 도면을 확인하세요.</p>
      </div>

      <div className="section">
        {/* 통계 */}
        <div style={{ display:'flex', gap:'3rem', marginBottom:'3rem', paddingBottom:'2rem', borderBottom:'1px solid #E8E4DC' }}>
          {[
            { num: drawings.length, label: '총 도면 수' },
            { num: drawings.filter(d => d.type === 'block_diagram').length, label: '블록도' },
            { num: drawings.filter(d => d.type === 'flowchart').length, label: '흐름도' },
            { num: drawings.filter(d => d.grade === 'A').length, label: 'A등급' },
          ].map(s => (
            <div key={s.label}>
              <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.8rem', fontWeight:200, color:'#0A0A16' }}>{s.num}</div>
              <div style={{ fontSize:'.72rem', color:'#999', letterSpacing:'.08em', textTransform:'uppercase', marginTop:'3px' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* 필터 */}
        <div className="gallery-filter">
          {typeFilters.map(f => (
            <button
              key={f.id}
              className={`gallery-filter-btn ${filter === f.id ? 'active' : ''}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* 그리드 */}
        <div className="gallery-grid">
          {filtered.map(d => (
            <div key={d.id} className="gallery-card" onClick={() => setSelected(d)}>
              <div className="gallery-svg-wrap">
                <img src={d.file} alt={d.title} />
              </div>
              <div className="gallery-card-body">
                <div className="gallery-type">{d.typeLabel}</div>
                <div className="gallery-title">{d.title}</div>
                <div className="gallery-desc">{d.desc}</div>
                <div className="gallery-meta">
                  <span className={`gallery-grade grade-${d.grade}`}>{d.grade}등급</span>
                  <span className="gallery-score">{d.score}점</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 하단 CTA */}
        <div style={{ marginTop:'3rem', background:'#08081A', padding:'3rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'1.5rem' }}>
          <div>
            <div style={{ color:'#C9A84C', fontSize:'.7rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'.5rem' }}>DRAWING AGENT</div>
            <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.4rem', fontWeight:300, color:'#F0EDE6', marginBottom:'.3rem' }}>
              내 발명의 도면을 자동 생성해보세요
            </div>
            <div style={{ color:'#555577', fontSize:'.86rem' }}>명세서 텍스트만 입력하면 30초 안에 완성됩니다.</div>
          </div>
          <Link href="/service/drawing" style={{ display:'inline-block', padding:'.9rem 2.5rem', border:'1px solid #C9A84C', color:'#C9A84C', fontSize:'.82rem', fontWeight:700, letterSpacing:'.1em', textDecoration:'none', whiteSpace:'nowrap' }}>
            도면 생성 서비스 →
          </Link>
        </div>
      </div>

      {/* 모달 */}
      {selected && (
        <div className="gallery-modal-bg" onClick={() => setSelected(null)}>
          <div className="gallery-modal" onClick={e => e.stopPropagation()}>
            <div className="gallery-modal-header">
              <div>
                <div style={{ color:'#C9A84C', fontSize:'.65rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'3px' }}>{selected.typeLabel}</div>
                <div className="gallery-modal-title">{selected.title}</div>
              </div>
              <button className="gallery-modal-close" onClick={() => setSelected(null)}>×</button>
            </div>
            <div className="gallery-modal-body">
              <img src={selected.file} alt={selected.title} />
            </div>
            <div className="gallery-modal-footer">
              <a className="gallery-dl-btn" href={selected.file} download={`${selected.id}.svg`}>
                SVG 다운로드
              </a>
              <button className="gallery-dl-btn outline" onClick={() => setSelected(null)}>
                닫기
              </button>
              <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:'.5rem' }}>
                <span className={`gallery-grade grade-${selected.grade}`}>{selected.grade}등급</span>
                <span style={{ color:'#999', fontSize:'.78rem' }}>{selected.score}점 / 100점</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}
