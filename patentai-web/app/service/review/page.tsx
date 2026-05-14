'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export default function Page() {
  return (
    <div className="site">
      <style>{`
        .det-wrap{padding:3.5rem 6rem;max-width:960px;margin:0 auto;}
        .det-section{margin-bottom:3rem;padding-bottom:3rem;border-bottom:1px solid #E8E4DC;}
        .det-kicker{font-size:.65rem;font-weight:700;letter-spacing:.3em;color:#C9A84C;margin-bottom:.6rem;}
        .det-h2{font-family:'Noto Serif KR',serif;font-size:1.5rem;font-weight:300;color:#0A0A16;margin-bottom:1rem;}
        .det-p{font-size:.9rem;color:#444;line-height:2;word-break:keep-all;margin-bottom:.9rem;}
        .det-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#E0DDD8;margin:1.2rem 0;}
        .det-cell{background:white;padding:1.2rem;}
        .det-cell-label{font-size:.62rem;font-weight:700;letter-spacing:.15em;color:#C9A84C;margin-bottom:.3rem;}
        .det-cell-value{font-size:.86rem;color:#222;line-height:1.7;word-break:keep-all;}
        .det-step{display:flex;gap:1rem;margin-bottom:1rem;}
        .det-step-num{width:34px;height:34px;border:1px solid rgba(201,168,76,.3);display:flex;align-items:center;justify-content:center;font-family:'Noto Serif KR',serif;color:#C9A84C;font-size:.78rem;flex-shrink:0;}
        .det-step-title{font-weight:700;font-size:.9rem;color:#0A0A16;margin-bottom:.3rem;}
        .det-step-desc{font-size:.84rem;color:#555;line-height:1.85;word-break:keep-all;}
        .det-code{background:#F0EDE8;border-left:3px solid #C9A84C;padding:.85rem 1.2rem;font-family:monospace;font-size:.8rem;color:#333;margin:1rem 0;line-height:1.8;}
        .det-table{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.84rem;}
        .det-table th{background:#08081A;color:#C9A84C;padding:.65rem 1rem;text-align:left;font-size:.68rem;letter-spacing:.12em;font-weight:700;}
        .det-table td{padding:.65rem 1rem;border-bottom:1px solid #E8E4DC;color:#333;line-height:1.7;word-break:keep-all;}
        .det-table tr:last-child td{border-bottom:none;}
        .det-table tr:nth-child(even) td{background:#FAFAF8;}
        .qa-item{border:1px solid #E8E4DC;margin-bottom:.5rem;}
        .qa-q{font-size:.88rem;font-weight:700;color:#0A0A16;padding:1rem 1.2rem;}
        .qa-a{font-size:.83rem;color:#555;line-height:1.85;padding:.2rem 1.2rem 1rem;word-break:keep-all;}
        @media(max-width:900px){.det-wrap{padding:2rem 1.5rem;}.det-grid{grid-template-columns:1fr;}}
      `}</style>

      <Nav />
      <div className="hero">
        <div className="tag">05 — REVIEW & INTEGRATION</div>
        <h1>심사 대응 · 통합 파이프라인</h1>
        <p>patent_generation_pipeline.py가 전체 에이전트를 하나의 흐름으로 연결하고 최종 특허 문서를 생성합니다.</p>
      </div>

      <div className="det-wrap">

        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">patent_generation_pipeline.py — 통합 오케스트레이터</div>
          <div className="det-p">
            <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>patent_generation_pipeline.py</code>의 <strong>run_full_pipeline()</strong>이 drawing_agent와 embodiment_agent를 순서대로 호출하여 최종 <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>final_patent_document_payload.json</code>을 생성합니다.
          </div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">실시예 생성 모델</div><div className="det-cell-value">gpt-4o-mini (temperature=0.2) — 명세서 실시예 작성</div></div>
            <div className="det-cell"><div className="det-cell-label">심사 대응 모델</div><div className="det-cell-value">gpt-4o — OA 분석 및 의견서 초안</div></div>
            <div className="det-cell"><div className="det-cell-label">통합 입력</div><div className="det-cell-value">invention_output + claim_output + drawing_results</div></div>
            <div className="det-cell"><div className="det-cell-label">최종 출력</div><div className="det-cell-value">final_patent_document_payload.json</div></div>
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">EMBODIMENT AGENT — embodiment_agent.py</div>
          <div className="det-h2">도면 기반 발명의 설명 자동 생성</div>
          <div className="det-p">도면 생성 결과(DrawingResult 리스트)를 기반으로 각 도면에 대한 설명과 실시예를 자동 작성합니다. 도면의 elements·relations JSON을 직접 참조하여 도면부호를 자연스럽게 삽입합니다.</div>
          {[
            {n:'01', title:'generate_drawing_description_and_embodiments()', desc:'gpt-4o-mini에게 도면 설계 JSON(elements, relations)과 청구항을 함께 전달합니다. 명세서에 기재되지 않은 내용은 절대 추가하지 않도록 프롬프트로 제한합니다.'},
            {n:'02', title:'brief_description_of_drawings 생성', desc:'각 도면(도 1, 도 2...)에 대한 간단한 설명 1문장을 생성합니다. 예: "도 1은 본 발명의 일 실시예에 따른 이미지 분류 시스템의 전체 구성도이다."'},
            {n:'03', title:'embodiments 생성 — 2~5 단락', desc:'각 도면에 대해 2~5 단락의 상세 실시예를 작성합니다. 도면부호를 자연스럽게 삽입하며(예: "입력부(110)는..."), 청구항의 기술적 특징을 기반으로 작성합니다.'},
            {n:'04', title:'generate_and_save_embodiment_output()', desc:'생성된 실시예를 drawing_analysis/{출원번호}/embodiment_output.json에 저장합니다. 전체 파이프라인의 마지막 단계로 final_patent_document_payload.json에 통합됩니다.'},
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>

        <div className="det-section">
          <div className="det-kicker">SYSTEM PROMPT — 실시예 생성 규칙</div>
          <div className="det-h2">embodiment_agent.py 핵심 프롬프트 규칙</div>
          <div className="det-code">
            규칙 1: 청구항에 없는 내용은 절대 추가하지 말 것<br/>
            규칙 2: 도면 fig_json의 elements/relations을 직접 참조<br/>
            규칙 3: 도면부호를 자연스럽게 삽입 예: "(110): 입력부"<br/>
            규칙 4: 도면 1개당 brief_description 1개 + embodiment 1개<br/>
            규칙 5: 실시예는 2~5 단락으로 작성<br/>
            규칙 6: 특허청 명세서 문체 사용 (수동태·명사형)
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">FULL PIPELINE OUTPUT</div>
          <div className="det-h2">최종 특허 문서 페이로드 구조</div>
          <div className="det-code">
            # build_patent_document_payload() 출력<br/>
            {'{'}<br/>
            &nbsp;&nbsp;"invention_output": {'{}'},    # 상담 에이전트 결과<br/>
            &nbsp;&nbsp;"claim_output": {'{}'},         # 청구항 에이전트 결과<br/>
            &nbsp;&nbsp;"drawings": [<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;{'{'}"fig_number": "도 1", "diagram_type": "block_diagram",<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"quality_score": 100, "quality_grade": "A",<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"svg_path": "drawing_analysis/.../fig_1.svg",<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"png_path": "..."{'}'}<br/>
            &nbsp;&nbsp;],<br/>
            &nbsp;&nbsp;"brief_description_of_drawings": [...],<br/>
            &nbsp;&nbsp;"embodiments": [...]<br/>
            {'}'}
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">REVIEW — 심사 대응</div>
          <div className="det-h2">GPT-4o 기반 OA 거절이유 분석</div>
          <div className="det-p">특허청 심사관의 거절이유 통지서(OA)를 GPT-4o로 분석합니다. 신규성(특허법 제29조 제1항)·진보성(제29조 제2항)·기재불비(제42조) 등 유형별로 분류하고 대응 전략을 제안합니다.</div>
          <table className="det-table">
            <thead><tr><th>거절 유형</th><th>근거 법조</th><th>대응 전략</th></tr></thead>
            <tbody>
              {[
                ['신규성 결여', '특허법 제29조 제1항', '청구범위 한정 — 선행기술과 차별되는 특징 추가'],
                ['진보성 결여', '특허법 제29조 제2항', '차별점 강조 의견서 — 기술적 효과 설명'],
                ['기재불비', '특허법 제42조', '명세서 보완 — 실시예·도면 추가 기재'],
                ['선행기술 결합', '특허법 제29조 제2항', '결합 곤란성 주장 — 기술 분야 차이 강조'],
              ].map(([t, l, s]) => (
                <tr key={t}><td>{t}</td><td style={{fontSize:'.78rem',color:'#888'}}>{l}</td><td>{s}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            {q:'embodiment_agent가 도면 fig_json을 직접 참조하는 이유는?', a:'단순히 텍스트만 보고 실시예를 쓰면 도면부호와 명세서가 불일치할 수 있습니다. fig_json의 elements 배열에서 실제 구성요소 이름과 ref_no를 읽어서 정확한 도면부호를 삽입합니다.'},
            {q:'최종 페이로드를 어떻게 활용하나요?', a:'final_patent_document_payload.json에는 청구항·도면·실시예가 모두 포함됩니다. 이 파일을 변리사에게 전달하면 최종 검토 후 특허청에 출원하는 기초 자료로 활용됩니다.'},
            {q:'파이프라인 전체 실행 시간은 얼마나 걸리나요?', a:'상담(5~10분) + 선행기술조사(2~5분) + 청구항생성(3~7분) + 도면생성(1~4분) + 실시예(2~3분)으로 총 13~29분 내에 완전한 특허 명세서 초안이 완성됩니다.'},
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>

        <div style={{display:'flex',gap:'1rem',flexWrap:'wrap'}}>
          <Link href="/contact" style={{display:'inline-block',padding:'.85rem 2rem',background:'#111128',border:'1px solid #111128',color:'#C9A84C',fontSize:'.8rem',fontWeight:700}}>상담 신청하기 →</Link>
          <Link href="/gallery" style={{display:'inline-block',padding:'.85rem 2rem',border:'1px solid #E8E4DC',color:'#444',fontSize:'.8rem'}}>도면 갤러리</Link>
          <Link href="/service" style={{display:'inline-block',padding:'.85rem 2rem',border:'1px solid #E8E4DC',color:'#444',fontSize:'.8rem'}}>서비스 전체 보기</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
