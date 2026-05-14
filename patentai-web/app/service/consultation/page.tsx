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
        .det-badge{display:inline-block;border:1px solid rgba(201,168,76,.3);color:#C9A84C;font-size:.68rem;padding:2px 8px;margin:.2rem;}
        @media(max-width:900px){.det-wrap{padding:2rem 1.5rem;}.det-grid{grid-template-columns:1fr;}}
      `}</style>

      <Nav />
      <div className="hero">
        <div className="tag">01 — CONSULTATION AGENT</div>
        <h1>특허 상담 에이전트</h1>
        <p>발명 내용을 자유롭게 설명하면 GPT-4o가 문제점·해결수단·차별성·효과를 구조화합니다.</p>
      </div>

      <div className="det-wrap">

        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">PatentConsultant 클래스 기반 2-Phase 상담 시스템</div>
          <div className="det-p">
            <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>agents/consultation/consultation_agent.py</code>의 <strong>PatentConsultant</strong> 클래스로 구현됩니다. 2단계 Phase로 구성되며, Phase 1에서 핵심 4요소를 수집하고 Phase 2에서 심화 기술 스펙을 수집합니다.
          </div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">추출 모델</div><div className="det-cell-value">gpt-4o (EXTRACT_MODEL) — 사용자 응답에서 발명 요소 추출</div></div>
            <div className="det-cell"><div className="det-cell-label">질문 생성 모델</div><div className="det-cell-value">gpt-4o-mini (CHAT_MODEL) — 비용 최적화된 질문 생성</div></div>
            <div className="det-cell"><div className="det-cell-label">정제 모델</div><div className="det-cell-value">gpt-4o (POLISH_MODEL) — 최종 명세서 품질 향상</div></div>
            <div className="det-cell"><div className="det-cell-label">DB</div><div className="det-cell-value">Supabase PostgreSQL — consulting, algorithm_steps, detail_elements 테이블</div></div>
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">PHASE 1 — 핵심 4요소 수집</div>
          <div className="det-h2">FIELD_LABELS 기반 구조화</div>
          <div className="det-p">코드에서 <strong>FIELD_LABELS</strong>로 정의된 4개 필드를 순서대로 수집합니다. GPT-4o가 사용자의 자유로운 설명에서 각 필드를 자동 추출합니다.</div>
          <table className="det-table">
            <thead><tr><th>필드</th><th>설명</th><th>예시</th></tr></thead>
            <tbody>
              {[
                ['problem', '기존 기술의 문제점', '기존 카드 비교 서비스는 단순 스펙 나열에 그쳐...'],
                ['solution', '해결 방법 (발명의 핵심)', 'GPT Vision OCR로 카드 약관 PDF를 정밀 분석하여...'],
                ['differentiation', '기존 기술과의 차별점', 'RAIchU는 실제 소비 데이터를 활용하여 개인화...'],
                ['effect', '기대 효과', '카드 추천 정확도 향상, 사용자 맞춤 서비스 제공...'],
              ].map(([f, d, e]) => (
                <tr key={f}><td><code style={{fontSize:'.78rem'}}>{f}</code></td><td>{d}</td><td style={{color:'#888',fontSize:'.78rem'}}>{e}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="det-p">완성도가 일정 수준(80% 이상)에 도달하면 알고리즘 단계 수집으로 자동 전환됩니다.</div>
        </div>

        <div className="det-section">
          <div className="det-kicker">ALGORITHM STEPS — 단계별 알고리즘 수집</div>
          <div className="det-h2">AlgorithmStep DB 테이블 저장</div>
          <div className="det-p">소프트웨어·방법 발명의 핵심 알고리즘을 단계별로 수집합니다. 최소 3단계 이상 입력해야 하며, "완료" 입력 시 저장됩니다.</div>
          <div className="det-code">
            # ALGO_EXIT_KEYWORDS — 수집 종료 키워드<br/>
            ["완료", "끝", "종료", "save", "done", "complete"]<br/><br/>
            # DB 저장 구조<br/>
            AlgorithmStep(user_id, consultation_idx, step_order, step_text)
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">PHASE 2 — 심화 기술 스펙 수집</div>
          <div className="det-h2">5개 추가 필드 수집</div>
          <div className="det-p">Phase 2에서는 명세서 실시예 작성에 필요한 상세 기술 정보를 수집합니다. 아래 키워드가 입력되면 해당 필드는 건너뜁니다.</div>
          <div className="det-code">
            # PHASE2_SKIP_KEYWORDS<br/>
            ["모르", "없어", "없음", "나중에", "패스", "skip", "생략"]
          </div>
          <table className="det-table">
            <thead><tr><th>필드</th><th>설명</th></tr></thead>
            <tbody>
              {[
                ['implementations', '구현 수단 (프레임워크, 언어, 인프라)'],
                ['parameters', '파라미터·데이터 구조·DB 스키마'],
                ['algorithms', '핵심 알고리즘 (수식, 모델, 아키텍처)'],
                ['optional_features', '부가 기능 (확장 가능한 선택 기능)'],
                ['error_handling', '예외 처리·장애 대응 로직'],
              ].map(([f, d]) => (
                <tr key={f}><td><code style={{fontSize:'.78rem'}}>{f}</code></td><td>{d}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="det-section">
          <div className="det-kicker">FILE UPLOAD — 문서 파싱</div>
          <div className="det-h2">PDF · DOCX · HWP 자동 파싱</div>
          <div className="det-p"><code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>document_utils.py</code>의 유틸리티 함수로 첨부 파일에서 발명 관련 텍스트를 자동 추출합니다.</div>
          <div className="det-code">
            extract_text_from_pdf(file_path)   # pymupdf 활용<br/>
            extract_text_from_docx(file_path)  # python-docx<br/>
            extract_text_from_hwp(file_path)   # hwp 전용 파서<br/>
            extract_images_from_pdf(file_path) # 이미지 추출 → GPT-4o Vision 분석
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">DB SCHEMA</div>
          <div className="det-h2">Supabase PostgreSQL 저장 구조</div>
          <table className="det-table">
            <thead><tr><th>테이블</th><th>주요 컬럼</th><th>설명</th></tr></thead>
            <tbody>
              {[
                ['consulting', 'user_id, consultation_idx, raw_chat_log, summary_problem, summary_solution, summary_differentiation, summary_effect', '상담 세션 전체 저장'],
                ['algorithm_steps', 'user_id, consultation_idx, step_order, step_text', '알고리즘 단계별 저장'],
                ['detail_elements', 'user_id, consultation_idx, element_type, element_value', '심화 기술 스펙 저장'],
              ].map(([t, c, d]) => (
                <tr key={t}><td><code style={{fontSize:'.78rem'}}>{t}</code></td><td style={{fontSize:'.76rem',color:'#888'}}>{c}</td><td>{d}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            { q:'gpt-4o와 gpt-4o-mini를 같이 쓰는 이유는?', a:'추출·분석처럼 정확도가 중요한 작업은 gpt-4o를, 단순 질문 생성처럼 비용 부담이 큰 반복 작업은 gpt-4o-mini를 사용하여 품질과 비용을 동시에 최적화합니다.' },
            { q:'상담이 중간에 끊겨도 다시 이어서 할 수 있나요?', a:'Supabase DB에 실시간 저장되므로 세션이 끊겨도 동일한 user_id와 consultation_idx로 재접속하면 이어서 진행할 수 있습니다.' },
            { q:'Phase 2 정보를 나중에 추가할 수 있나요?', a:'PHASE2_SKIP_KEYWORDS를 사용해 건너뛴 필드는 나중에 보완할 수 있습니다. 상담 완료 후에도 detail_elements 테이블에 직접 추가가 가능합니다.' },
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>

        <div style={{display:'flex',gap:'1rem',flexWrap:'wrap'}}>
          <Link href="/service/prior-art" style={{display:'inline-block',padding:'.85rem 2rem',background:'#111128',border:'1px solid #111128',color:'#C9A84C',fontSize:'.8rem',fontWeight:700}}>다음: 선행기술 조사 →</Link>
          <Link href="/contact" style={{display:'inline-block',padding:'.85rem 2rem',border:'1px solid #E8E4DC',color:'#444',fontSize:'.8rem'}}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
