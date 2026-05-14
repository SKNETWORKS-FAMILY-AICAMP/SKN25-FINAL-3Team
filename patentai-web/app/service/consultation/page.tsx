import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export default function Page() {
  return (
    <div className="site">
      <style>{`
        .det-section { margin-bottom:3rem; padding-bottom:3rem; border-bottom:1px solid #E8E4DC; }
        .det-kicker { font-size:.65rem; font-weight:700; letter-spacing:.3em; color:#C9A84C; margin-bottom:.6rem; }
        .det-h2 { font-family:'Noto Serif KR',serif; font-size:1.6rem; font-weight:300; color:#0A0A16; margin-bottom:1rem; }
        .det-p { font-size:.9rem; color:#444; line-height:2; word-break:keep-all; margin-bottom:1rem; }
        .det-list { list-style:none; padding:0; display:flex; flex-direction:column; gap:.5rem; margin-bottom:1.2rem; }
        .det-list li { display:flex; gap:.7rem; font-size:.88rem; color:#333; line-height:1.7; }
        .det-list li::before { content:'—'; color:#C9A84C; flex-shrink:0; }
        .det-grid { display:grid; grid-template-columns:1fr 1fr; gap:1px; background:#E0DDD8; margin:1.2rem 0; }
        .det-cell { background:white; padding:1.2rem; }
        .det-cell-label { font-size:.62rem; font-weight:700; letter-spacing:.15em; color:#C9A84C; margin-bottom:.3rem; }
        .det-cell-value { font-size:.86rem; color:#222; line-height:1.7; word-break:keep-all; }
        .det-step { display:flex; gap:1rem; margin-bottom:1rem; }
        .det-step-num { width:34px; height:34px; border:1px solid rgba(201,168,76,.3); display:flex; align-items:center; justify-content:center; font-family:'Noto Serif KR',serif; color:#C9A84C; font-size:.78rem; flex-shrink:0; }
        .det-step-title { font-weight:700; font-size:.88rem; color:#0A0A16; margin-bottom:.3rem; }
        .det-step-desc { font-size:.83rem; color:#555; line-height:1.8; word-break:keep-all; }
        .qa-item { border:1px solid #E8E4DC; margin-bottom:.5rem; }
        .qa-q { font-size:.88rem; font-weight:700; color:#0A0A16; padding:1rem 1.2rem; }
        .qa-a { font-size:.83rem; color:#555; line-height:1.85; padding:.2rem 1.2rem 1rem; word-break:keep-all; }
        @media(max-width:900px){ .det-grid { grid-template-columns:1fr; } }
      `}</style>

      <Nav />
      <div className="hero">
        <div className="tag">01 — CONSULTATION AGENT</div>
        <h1>특허 상담<br/>에이전트</h1>
        <p>발명 내용을 자유롭게 설명하면 AI가 문제점·해결수단·효과·구성요소를 체계적으로 구조화합니다.</p>
      </div>

      <div style={{ padding:'3.5rem 6rem', maxWidth:900, margin:'0 auto' }}>

        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">상담 에이전트란?</div>
          <div className="det-p">PatentAI 상담 에이전트는 GPT-4o 기반 대화형 인터페이스로 발명 내용을 단계적으로 수집하고 구조화합니다. 기술적 배경 없이도 발명 아이디어만 있으면 특허 출원에 필요한 모든 정보를 AI가 정리해 드립니다.</div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">AI 모델</div><div className="det-cell-value">GPT-4o (분석·구조화)</div></div>
            <div className="det-cell"><div className="det-cell-label">처리 시간</div><div className="det-cell-value">5–10분 (대화 길이에 따라)</div></div>
            <div className="det-cell"><div className="det-cell-label">파일 지원</div><div className="det-cell-value">PDF · DOCX · HWP 업로드</div></div>
            <div className="det-cell"><div className="det-cell-label">저장</div><div className="det-cell-value">Supabase PostgreSQL DB</div></div>
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">HOW IT WORKS</div>
          <div className="det-h2">동작 원리</div>
          {[
            { n:'01', title:'1부 — 핵심 정보 수집', desc:'발명의 제목·기술분야·기존 기술의 문제점·해결 방법·기대효과·구성요소를 단계별 질문으로 수집합니다. 사용자가 자유롭게 설명하면 GPT-4o가 자동으로 각 항목을 추출합니다.' },
            { n:'02', title:'알고리즘 단계 수집', desc:'소프트웨어·방법 발명의 경우 작동 순서를 단계별로 입력받습니다. 최소 3단계 이상을 입력하면 특허 명세서의 알고리즘 설명 섹션에 사용됩니다.' },
            { n:'03', title:'2부 — 심화 정보 수집', desc:'구현 수단·파라미터·핵심 알고리즘·부가 기능·예외 처리 등 상세 기술 내용을 추가로 수집합니다. 이 정보는 명세서 실시예 작성에 활용됩니다.' },
            { n:'04', title:'최종 요약 확인 및 저장', desc:'수집된 모든 정보를 GPT-4o로 정제하여 특허 명세서 형식에 맞게 구조화합니다. 확인 후 Supabase DB에 저장하며 이후 단계(선행기술 조사·명세서 작성·도면 생성)로 자동 연계됩니다.' },
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>

        <div className="det-section">
          <div className="det-kicker">OUTPUT</div>
          <div className="det-h2">출력 결과</div>
          <ul className="det-list">
            <li>발명 구조화 JSON (title, problem, solution, differentiation, effect, algorithm_steps, implementations 등)</li>
            <li>상담 대화 로그 (원문 보존)</li>
            <li>Supabase consultation 테이블 저장 (user_id, consultation_idx, raw_chat_log, summary)</li>
            <li>다음 단계 자동 연계 (선행기술 조사·청구항 생성·도면 생성)</li>
          </ul>
        </div>

        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            { q:'기술적 지식이 없어도 사용할 수 있나요?', a:'네. AI가 단계별 질문으로 안내하기 때문에 발명 아이디어만 있으면 충분합니다. 전문 용어를 몰라도 일상 언어로 설명하시면 됩니다.' },
            { q:'상담 내용은 안전하게 보호되나요?', a:'모든 상담 내용은 Supabase AES-256 암호화로 저장됩니다. 제3자 공유는 일절 없으며 개인정보보호법을 준수합니다.' },
            { q:'PDF 첨부 파일의 내용도 분석되나요?', a:'네. pymupdf로 PDF 텍스트를 추출하고 GPT-4o로 발명 정보를 자동 파싱합니다. DOCX·HWP 형식도 지원합니다.' },
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>

        <div style={{ display:'flex', gap:'1rem' }}>
          <Link href="/service/prior-art" style={{ display:'inline-block', padding:'.85rem 2rem', background:'#111128', border:'1px solid #111128', color:'#C9A84C', fontSize:'.8rem', fontWeight:700 }}>다음: 선행기술 조사 →</Link>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2rem', border:'1px solid #E8E4DC', color:'#444', fontSize:'.8rem' }}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
