'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'
import { useState } from 'react'

const drawings = [
  { file:'/drawings/sample_block.svg', type:'BLOCK DIAGRAM', title:'이미지 분류 시스템 구성도', grade:'A', score:100 },
  { file:'/drawings/sample_flow.svg',  type:'FLOWCHART',     title:'이미지 분류 처리 흐름도',  grade:'A', score:95  },
  { file:'/drawings/patent_block.svg', type:'BLOCK DIAGRAM', title:'문장 제공 장치 구성도',     grade:'A', score:90  },
  { file:'/drawings/patent_flow.svg',  type:'FLOWCHART',     title:'문장 제공 방법 흐름도',     grade:'B', score:85  },
  { file:'/drawings/ai_block.svg',     type:'BLOCK DIAGRAM', title:'AI 시스템 구성도',          grade:'A', score:100 },
  { file:'/drawings/ai_flow.svg',      type:'FLOWCHART',     title:'AI 처리 흐름도',            grade:'A', score:100 },
  { file:'/drawings/rag_block.svg',    type:'BLOCK DIAGRAM', title:'RAG 시스템 구성도',         grade:'A', score:100 },
  { file:'/drawings/rag_flow.svg',     type:'FLOWCHART',     title:'RAG 처리 흐름도',           grade:'A', score:100 },
]

function GalleryInline() {
  const [selected, setSelected] = useState<typeof drawings[0] | null>(null)
  return (
    <>
      <div className="gallery-inline">
        {drawings.map((d, i) => (
          <div key={i} className="gi-card" onClick={() => setSelected(d)}>
            <img className="gi-img" src={d.file} alt={d.title} />
            <div className="gi-body">
              <div className="gi-type">{d.type}</div>
              <div className="gi-title">{d.title}</div>
              <div className="gi-meta">{d.grade}등급 · {d.score}점</div>
            </div>
          </div>
        ))}
      </div>
      {selected && (
        <div className="gi-modal-bg" onClick={() => setSelected(null)}>
          <div className="gi-modal" onClick={e => e.stopPropagation()}>
            <div className="gi-modal-hd">
              <div className="gi-modal-title">{selected.title}</div>
              <button className="gi-modal-close" onClick={() => setSelected(null)}>×</button>
            </div>
            <div className="gi-modal-body">
              <img src={selected.file} alt={selected.title} />
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default function DrawingPage() {
  return (
    <div className="site">
      <style>{`
        .detail-layout { display:grid; grid-template-columns:260px 1fr; gap:0; align-items:start; }
        .detail-aside { position:sticky; top:80px; padding:2.5rem 0; border-right:1px solid #E0DDD8; background:white; }
        .aside-section { padding:.5rem 0; border-bottom:1px solid #F0EDE8; }
        .aside-section:last-child { border-bottom:none; }
        .aside-label { padding:.5rem 1.8rem; font-size:.62rem; font-weight:700; letter-spacing:.2em; color:#C9A84C; }
        .aside-link { display:block; padding:.5rem 1.8rem; font-size:.8rem; color:#666; text-decoration:none; transition:.12s; }
        .aside-link:hover { color:#0A0A16; background:#F7F6F3; }
        .detail-main { padding:3.5rem 4rem; max-width:860px; }
        .det-section { margin-bottom:3.5rem; padding-bottom:3.5rem; border-bottom:1px solid #E8E4DC; }
        .det-section:last-child { border-bottom:none; }
        .det-kicker { font-size:.65rem; font-weight:700; letter-spacing:.3em; color:#C9A84C; margin-bottom:.6rem; }
        .det-h2 { font-family:'Noto Serif KR',serif; font-size:1.6rem; font-weight:300; color:#0A0A16; margin-bottom:1rem; }
        .det-lead { font-size:.95rem; color:#555; line-height:2; word-break:keep-all; margin-bottom:1.5rem; }
        .det-p { font-size:.9rem; color:#444; line-height:2; word-break:keep-all; margin-bottom:1rem; }
        .det-list { margin:0 0 1.2rem; padding-left:0; list-style:none; display:flex; flex-direction:column; gap:.5rem; }
        .det-list li { display:flex; align-items:flex-start; gap:.7rem; font-size:.88rem; color:#333; line-height:1.7; }
        .det-list li::before { content:'—'; color:#C9A84C; flex-shrink:0; margin-top:2px; }
        .det-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; background:#E0DDD8; margin:1.5rem 0; }
        .det-cell { background:white; padding:1.4rem; }
        .det-cell-label { font-size:.65rem; font-weight:700; letter-spacing:.15em; color:#C9A84C; margin-bottom:.4rem; }
        .det-cell-value { font-size:.88rem; color:#222; line-height:1.7; word-break:keep-all; }
        .det-step { display:flex; gap:1.2rem; align-items:flex-start; margin-bottom:1.2rem; }
        .det-step-num { width:36px; height:36px; border:1px solid rgba(201,168,76,.3); display:flex; align-items:center; justify-content:center; font-family:'Noto Serif KR',serif; color:#C9A84C; font-size:.8rem; flex-shrink:0; }
        .det-step-body { flex:1; }
        .det-step-title { font-weight:700; font-size:.9rem; color:#0A0A16; margin-bottom:.3rem; }
        .det-step-desc { font-size:.84rem; color:#555; line-height:1.8; word-break:keep-all; }
        .det-code { background:#F0EDE8; border-left:3px solid #C9A84C; padding:.8rem 1.2rem; font-family:monospace; font-size:.82rem; color:#333; margin:1rem 0; line-height:1.7; }
        .det-badge { display:inline-block; border:1px solid rgba(201,168,76,.3); color:#C9A84C; font-size:.68rem; padding:2px 8px; margin-right:.4rem; margin-bottom:.4rem; }
        .img-box { border:1px solid #E8E4DC; padding:.5rem; margin:1rem 0; background:white; }
        .img-box img { width:100%; height:auto; display:block; }
        .img-caption { font-size:.72rem; color:#999; text-align:center; margin-top:.4rem; letter-spacing:.06em; }
        .qa-item { border:1px solid #E8E4DC; margin-bottom:.5rem; }
        .qa-q { font-size:.88rem; font-weight:700; color:#0A0A16; padding:1rem 1.2rem; }
        .qa-a { font-size:.84rem; color:#555; line-height:1.85; padding:.2rem 1.2rem 1rem; word-break:keep-all; }
        .ref-badge { display:inline-block; background:#F0EDE8; color:#888; font-size:.68rem; padding:1px 7px; margin-left:.5rem; }
        @media(max-width:900px){ .detail-layout { grid-template-columns:1fr; } .detail-aside { position:static; } .detail-main { padding:2rem 1.5rem; } .det-grid { grid-template-columns:1fr; } }
      `}</style>

      <Nav />

      {/* 히어로 */}
      <div className="hero" style={{ borderLeft:'4px solid #C9A84C' }}>
        <div className="tag">04 — DRAWING AGENT</div>
        <h1>도면 자동 생성<br/>에이전트</h1>
        <p>명세서 텍스트만으로 특허청 실무 수준의 SVG 도면을 30초 내 자동 생성합니다.</p>
        <div style={{ display:'flex', gap:'1rem', marginTop:'2rem', flexWrap:'wrap' }}>
          <Link href="/gallery" style={{ display:'inline-block', padding:'.7rem 1.8rem', border:'1px solid #C9A84C', color:'#C9A84C', fontSize:'.78rem', fontWeight:700, letterSpacing:'.08em' }}>도면 갤러리 보기 →</Link>
          <Link href="/contact" style={{ display:'inline-block', padding:'.7rem 1.8rem', border:'1px solid rgba(201,168,76,.3)', color:'#9999B8', fontSize:'.78rem', letterSpacing:'.08em' }}>상담 신청</Link>
        </div>
      </div>

      <div className="detail-layout">
        {/* 사이드바 목차 */}
        <aside className="detail-aside">
          <div className="aside-section">
            <div className="aside-label">OVERVIEW</div>
            <a className="aside-link" href="#overview">개요</a>
            <a className="aside-link" href="#features">주요 기능</a>
            <a className="aside-link" href="#types">지원 도면 유형</a>
          </div>
          <div className="aside-section">
            <div className="aside-label">HOW IT WORKS</div>
            <a className="aside-link" href="#pipeline">처리 파이프라인</a>
            <a className="aside-link" href="#quality">품질 검증 시스템</a>
            <a className="aside-link" href="#tech">기술 스택</a>
          </div>
          <div className="aside-section">
            <div className="aside-label">SAMPLES</div>
            <a className="aside-link" href="#samples">도면 샘플</a>
            <a className="aside-link" href="#spec">특허청 기준</a>
          </div>
          <div className="aside-section">
            <div className="aside-label">USAGE</div>
            <a className="aside-link" href="#usage">사용 방법</a>
            <a className="aside-link" href="#faq">자주 묻는 질문</a>
          </div>
        </aside>

        {/* 메인 콘텐츠 */}
        <div className="detail-main">

          {/* 개요 */}
          <div className="det-section" id="overview">
            <div className="det-kicker">OVERVIEW</div>
            <div className="det-h2">도면 에이전트란?</div>
            <div className="det-lead">
              PatentAI 도면 에이전트는 특허 명세서 텍스트를 입력받아 특허청 제출 기준에 맞는 고품질 SVG 도면을 자동으로 생성하는 AI 시스템입니다.
            </div>
            <div className="det-p">
              기존에는 도면사나 변리사가 수작업으로 그리던 특허 도면을 AI가 30초~2분 내에 자동 생성합니다. GPT-4o-mini로 명세서를 분석하고, 좌표 기반 SVG 직접 렌더링 방식으로 도면부호·연결선·레이아웃을 자동으로 배치합니다.
            </div>

            <div className="det-grid">
              <div className="det-cell">
                <div className="det-cell-label">처리 시간</div>
                <div className="det-cell-value">30초 ~ 2분 (복잡도에 따라)</div>
              </div>
              <div className="det-cell">
                <div className="det-cell-label">품질 점수</div>
                <div className="det-cell-value">평균 85점 / A등급</div>
              </div>
              <div className="det-cell">
                <div className="det-cell-label">출력 형식</div>
                <div className="det-cell-value">SVG (벡터) + PNG (고해상도, 220dpi)</div>
              </div>
              <div className="det-cell">
                <div className="det-cell-label">AI 모델</div>
                <div className="det-cell-value">GPT-4o-mini (분석) + SVG 직접 렌더러</div>
              </div>
            </div>
          </div>

          {/* 주요 기능 */}
          <div className="det-section" id="features">
            <div className="det-kicker">FEATURES</div>
            <div className="det-h2">주요 기능</div>
            <ul className="det-list">
              <li><strong>5종 도면 유형 자동 분류</strong> — 블록도·흐름도·시퀀스·상태도·UI 화면도를 명세서 내용 기반으로 자동 선택</li>
              <li><strong>도면부호(참조번호) 자동 배치</strong> — 명세서 부호 설명을 파싱하여 인출선과 함께 자동 배치</li>
              <li><strong>특허청 형식 자동 준수</strong> — 흑백 선화, 여백·선 굵기·도면부호 크기 기준 자동 적용</li>
              <li><strong>품질 자동 검증 및 보정</strong> — 100점 만점 품질 점수 산출, 75점 미만 시 자동 보정 1회</li>
              <li><strong>Vision 검수 (선택)</strong> — GPT-4o Vision으로 생성된 도면을 이미지 분석하여 누락 요소 감지</li>
              <li><strong>배치 처리</strong> — 여러 특허 명세서를 한 번에 처리하는 배치 모드 지원</li>
            </ul>
          </div>

          {/* 도면 유형 */}
          <div className="det-section" id="types">
            <div className="det-kicker">DIAGRAM TYPES</div>
            <div className="det-h2">지원 도면 유형 5종</div>
            {[
              { type:'블록도', en:'Block Diagram', renderer:'patent_block_pro', desc:'시스템 구성요소 간의 관계와 구조를 표현합니다. 점선 시스템 경계박스로 내부/외부 모듈을 구분하며, 외부 엔티티(사용자·외부 서버)를 별도로 표시합니다.' },
              { type:'흐름도', en:'Flowchart', renderer:'patent_flow_pro', desc:'처리 절차나 알고리즘의 흐름을 표현합니다. 타원(시작/종료)·마름모(판단/분기)·사각형(처리)·평행사변형(입출력)을 사용하며 Yes/No 분기를 명시합니다.' },
              { type:'시퀀스 다이어그램', en:'Sequence Diagram', renderer:'patent_sequence_pro', desc:'여러 주체(클라이언트·서버·DB) 간의 메시지 교환 순서를 표현합니다. 생명선·활성화 박스·동기/비동기 화살표를 지원합니다.' },
              { type:'상태도', en:'State Diagram', renderer:'patent_state_pro', desc:'시스템 상태 전이를 표현합니다. 둥근 사각형 상태 노드, 초기 마커(검은 원), 종료 마커(이중 원)를 사용합니다.' },
              { type:'UI 화면도', en:'UI Screen Diagram', renderer:'patent_ui_pro', desc:'소프트웨어 인터페이스의 화면 구성을 표현합니다. 디바이스 프레임, 헤더/버튼/입력필드/리스트 등 UI 요소를 타입별로 렌더링합니다.' },
            ].map(item => (
              <div key={item.type} style={{ background:'white', border:'1px solid #E8E4DC', padding:'1.2rem 1.4rem', marginBottom:'.6rem' }}>
                <div style={{ display:'flex', alignItems:'center', gap:'.8rem', marginBottom:'.5rem' }}>
                  <span style={{ fontWeight:700, fontSize:'.9rem', color:'#0A0A16' }}>{item.type}</span>
                  <span style={{ color:'#999', fontSize:'.76rem' }}>{item.en}</span>
                  <code style={{ marginLeft:'auto', fontSize:'.68rem', background:'#F0EDE8', color:'#888', padding:'1px 6px' }}>{item.renderer}</code>
                </div>
                <div style={{ fontSize:'.85rem', color:'#555', lineHeight:1.8, wordBreak:'keep-all' }}>{item.desc}</div>
              </div>
            ))}
          </div>

          {/* 처리 파이프라인 */}
          <div className="det-section" id="pipeline">
            <div className="det-kicker">HOW IT WORKS</div>
            <div className="det-h2">처리 파이프라인</div>
            <div className="det-p">도면 에이전트는 다음 6단계로 동작합니다.</div>

            {[
              { n:'01', title:'명세서 파싱', desc:'특허 명세서에서 청구범위·도면 목록·부호 설명을 정규식으로 자동 추출합니다. 한글·영문 혼용 텍스트를 모두 처리합니다.' },
              { n:'02', title:'LLM 분석 (GPT-4o-mini)', desc:'추출된 텍스트를 GPT-4o-mini에 전달하여 구성요소(component)·처리 흐름(process_flow)·관계(relationships)를 JSON으로 구조화합니다. step_type(terminal/process/decision/io)을 자동 분류합니다.' },
              { n:'03', title:'도면 유형 자동 분류', desc:'분석된 발명 유형과 도면 제목 키워드를 기반으로 5종 도면 유형 중 최적 유형을 자동 선택합니다. ("순서도"→flowchart, "구성도"→block_diagram 등)' },
              { n:'04', title:'fig_json 설계', desc:'LLM 분석 결과를 바탕으로 도면 설계 JSON(elements, relations)을 생성합니다. 구성요소 우선순위 알고리즘으로 중요 요소를 앞에 배치합니다.' },
              { n:'05', title:'SVG 직접 렌더링', desc:'Python 기반 SVG 캔버스에 좌표 계산 후 직접 SVG 태그를 생성합니다. 도면부호 인출선, 연결 화살표, 다중 줄 텍스트를 처리합니다. 외부 라이브러리 없이 순수 Python으로 구현됐습니다.' },
              { n:'06', title:'품질 검증 및 보정', desc:'도면부호 완비 여부(±4점/개), 구성요소 수(3개 미만 -15점), 렌더러 메타데이터, 검증 오류를 자동 채점합니다. 75점 미만 시 LLM 기반 자동 보정 1회를 수행합니다.' },
            ].map(step => (
              <div key={step.n} className="det-step">
                <div className="det-step-num">{step.n}</div>
                <div className="det-step-body">
                  <div className="det-step-title">{step.title}</div>
                  <div className="det-step-desc">{step.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* 품질 검증 */}
          <div className="det-section" id="quality">
            <div className="det-kicker">QUALITY SYSTEM</div>
            <div className="det-h2">품질 검증 시스템</div>
            <div className="det-grid">
              {[
                { grade:'A', range:'90점 이상', color:'#27ae60', desc:'도면부호 완비, 구성요소 충분, 렌더러 정상 작동' },
                { grade:'B', range:'75점 이상', color:'#f39c12', desc:'통과 기준. 일부 보완이 가능하나 제출 가능 수준' },
                { grade:'C', range:'60점 이상', color:'#e67e22', desc:'검토 필요. 도면부호 일부 누락 또는 구성요소 부족' },
                { grade:'D', range:'60점 미만', color:'#e74c3c', desc:'자동 보정 대상. 1회 보정 후 재평가' },
              ].map(g => (
                <div key={g.grade} className="det-cell">
                  <div style={{ display:'flex', alignItems:'center', gap:'.6rem', marginBottom:'.4rem' }}>
                    <span style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.2rem', fontWeight:200, color:g.color }}>{g.grade}</span>
                    <span style={{ fontSize:'.72rem', color:'#999' }}>{g.range}</span>
                  </div>
                  <div className="det-cell-value">{g.desc}</div>
                </div>
              ))}
            </div>
            <div className="det-p">주요 감점 항목: 도면부호 없는 요소(−4점/개, 최대 −15점), 구성요소 3개 미만(−15점), 프로 렌더러 미사용(−10점), 검증 오류(−15점)</div>
          </div>

          {/* 기술 스택 */}
          <div className="det-section" id="tech">
            <div className="det-kicker">TECH STACK</div>
            <div className="det-h2">기술 스택</div>
            <div style={{ display:'flex', flexWrap:'wrap', gap:'.4rem', marginBottom:'1rem' }}>
              {['Python 3.12', 'OpenAI GPT-4o-mini', 'SVG 직접 렌더링', 'cairosvg', 'Pillow', 'pdf2image', 'GPT-4o Vision', 'Supabase'].map(t => (
                <span key={t} className="det-badge">{t}</span>
              ))}
            </div>
            <div className="det-code">
              # 실행 명령어<br/>
              python drawing_agent.py test          # 샘플 테스트<br/>
              python drawing_agent.py real          # 실제 특허 1건<br/>
              python drawing_agent.py run 10        # 배치 10건<br/>
              python drawing_agent.py run 10 --vision  # Vision 검수 포함
            </div>
          </div>

          {/* 도면 갤러리 */}
          <div className="det-section" id="samples">
            <div className="det-kicker">DRAWING GALLERY</div>
            <div className="det-h2">실제 생성 도면 갤러리</div>
            <div className="det-p">PatentAI 도면 에이전트가 실제 특허 명세서를 기반으로 자동 생성한 도면 샘플입니다. 클릭하면 크게 볼 수 있습니다.</div>
            <style>{`
              .gallery-inline { display:grid; grid-template-columns:repeat(2,1fr); gap:1px; background:#E0DDD8; margin:1rem 0; }
              .gi-card { background:white; cursor:pointer; transition:background .15s; overflow:hidden; }
              .gi-card:hover { background:#FAFAF8; }
              .gi-img { width:100%; aspect-ratio:4/3; object-fit:contain; padding:.5rem; background:#FEFEFE; border-bottom:1px solid #F0EDE8; display:block; }
              .gi-body { padding:1rem 1.2rem; }
              .gi-type { font-size:.6rem; font-weight:700; letter-spacing:.2em; color:#C9A84C; margin-bottom:.2rem; }
              .gi-title { font-size:.82rem; font-weight:700; color:#0A0A16; margin-bottom:.2rem; }
              .gi-meta { font-size:.72rem; color:#999; }
              .gi-modal-bg { position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:center;justify-content:center;padding:2rem; }
              .gi-modal { background:white;max-width:900px;width:100%;max-height:88vh;display:flex;flex-direction:column;overflow:hidden; }
              .gi-modal-hd { padding:1rem 1.4rem;border-bottom:1px solid #E8E4DC;display:flex;align-items:center;justify-content:space-between; }
              .gi-modal-title { font-weight:700;font-size:.95rem;color:#0A0A16; }
              .gi-modal-close { background:none;border:none;font-size:1.3rem;cursor:pointer;color:#999; }
              .gi-modal-body { flex:1;overflow:auto;padding:1rem; }
              .gi-modal-body img { width:100%;height:auto; }
              @media(max-width:600px){ .gallery-inline { grid-template-columns:1fr; } }
            `}</style>
            <GalleryInline />
          </div>

          {/* 특허청 기준 */}
          <div className="det-section" id="spec">
            <div className="det-kicker">PATENT OFFICE STANDARD</div>
            <div className="det-h2">특허청 도면 기준 준수</div>
            <ul className="det-list">
              <li>흑백 선화 (컬러 사용 불가 원칙 준수)</li>
              <li>A4 기준 여백: 상 2.5cm·하 1.0cm·좌 2.5cm·우 1.5cm</li>
              <li>선 굵기 0.2mm 이상, 문자 크기 3.2mm 이상</li>
              <li>도면부호(참조번호) 명시 및 부호의 설명 일치</li>
              <li>SVG → PNG(220dpi) 변환으로 고해상도 제출본 제공</li>
            </ul>
            <div style={{ fontSize:'.75rem', color:'#999', borderLeft:'2px solid #E8E4DC', paddingLeft:'.8rem', marginTop:'.5rem' }}>
              근거: 특허법 시행규칙 별지 제15호 서식, KS X ISO 5807 순서도 기호 표준
            </div>
          </div>

          {/* 사용 방법 */}
          <div className="det-section" id="usage">
            <div className="det-kicker">USAGE</div>
            <div className="det-h2">사용 방법</div>
            <div className="det-step">
              <div className="det-step-num">01</div>
              <div className="det-step-body">
                <div className="det-step-title">상담 에이전트에서 자동 실행</div>
                <div className="det-step-desc">특허 상담 및 청구항 생성이 완료되면 사이드바의 "특허 도면 자동 생성" 버튼을 클릭합니다. 상담 내용이 자동으로 명세서 텍스트로 변환되어 도면 생성에 사용됩니다.</div>
              </div>
            </div>
            <div className="det-step">
              <div className="det-step-num">02</div>
              <div className="det-step-body">
                <div className="det-step-title">Python CLI 직접 실행</div>
                <div className="det-step-desc">drawing_agent.py를 직접 실행할 수 있습니다. 특허 TXT 파일 또는 직접 텍스트를 입력받아 처리합니다.</div>
              </div>
            </div>
            <div className="det-step">
              <div className="det-step-num">03</div>
              <div className="det-step-body">
                <div className="det-step-title">결과물 확인 및 다운로드</div>
                <div className="det-step-desc">생성된 도면은 drawing_analysis/{'{출원번호}'} 폴더에 SVG·PNG·JSON·검증 리포트로 저장됩니다. 도면 갤러리에서 미리보기 및 다운로드가 가능합니다.</div>
              </div>
            </div>
          </div>

          {/* FAQ */}
          <div className="det-section" id="faq">
            <div className="det-kicker">FAQ</div>
            <div className="det-h2">자주 묻는 질문</div>
            {[
              { q:'명세서 없이 간단한 설명만으로도 도면이 생성되나요?', a:'네. 발명의 구성요소와 처리 흐름을 간략히 기술한 텍스트만으로도 도면을 생성할 수 있습니다. 상세한 명세서일수록 더 정확한 도면이 생성됩니다.' },
              { q:'생성된 도면을 특허청에 바로 제출할 수 있나요?', a:'PatentAI가 생성하는 도면은 특허청 형식 기준을 자동으로 준수합니다. 다만 최종 제출 전 전문 변리사의 검토를 권장합니다.' },
              { q:'흐름도에서 판단 분기(Yes/No)가 자동으로 표시되나요?', a:'네. 명세서에서 "여부", "판단", "확인" 등의 키워드를 감지하거나 step_type을 decision으로 분류하면 마름모 모양의 판단 노드와 Yes/No 분기가 자동으로 표시됩니다.' },
              { q:'도면 수정이 필요한 경우 어떻게 하나요?', a:'생성된 fig_json 파일을 수정한 후 렌더러를 재실행하면 됩니다. SVG 파일을 직접 편집하는 것도 가능합니다.' },
              { q:'한 번에 몇 개의 도면을 생성할 수 있나요?', a:'배치 모드(python drawing_agent.py run N)로 N건의 특허를 한 번에 처리할 수 있습니다. 각 특허당 최대 2개의 도면(전체 구성도 + 처리 흐름도)을 자동 생성합니다.' },
            ].map((item, i) => (
              <div key={i} className="qa-item">
                <div className="qa-q">Q. {item.q}</div>
                <div className="qa-a">A. {item.a}</div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div style={{ display:'flex', gap:'1rem', flexWrap:'wrap' }}>
            <Link href="/gallery" style={{ display:'inline-block', padding:'.9rem 2.2rem', background:'#111128', border:'1px solid #111128', color:'#C9A84C', fontSize:'.82rem', fontWeight:700, letterSpacing:'.08em' }}>
              도면 갤러리 보기
            </Link>
            <Link href="/contact" style={{ display:'inline-block', padding:'.9rem 2.2rem', border:'1px solid #E8E4DC', color:'#444', fontSize:'.82rem', letterSpacing:'.06em' }}>
              상담 신청하기 →
            </Link>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
