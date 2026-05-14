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
        <div className="tag">03 — SPECIFICATION & CLAIMS</div>
        <h1>명세서 · 청구항 에이전트</h1>
        <p>EXAONE-3.0-7.8B LoRA 파인튜닝 sLLM이 RunPod GPU 서버에서 청구항을 자동 생성합니다.</p>
      </div>

      <div className="det-wrap">

        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">claim_agent.py + RunPod EXAONE sLLM API</div>
          <div className="det-p">
            <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>agents/consultation/claim_agent.py</code>가 Supabase DB에서 상담 데이터를 재구성하고, <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>agents/runpod/main.py</code>의 FastAPI 엔드포인트를 호출하여 청구항을 생성합니다.
          </div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">청구항 생성 모델</div><div className="det-cell-value">EXAONE-3.0-7.8B + LoRA (특허 데이터 파인튜닝)</div></div>
            <div className="det-cell"><div className="det-cell-label">Fallback 모델</div><div className="det-cell-value">GPT-4o (sLLM 미연결 시 자동 전환)</div></div>
            <div className="det-cell"><div className="det-cell-label">배포 환경</div><div className="det-cell-value">RunPod GPU 서버 → FastAPI /generate-claims</div></div>
            <div className="det-cell"><div className="det-cell-label">LoRA 리포지토리</div><div className="det-cell-value">HuggingFace silverstone1004/claim</div></div>
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">CLAIM AGENT — 데이터 흐름</div>
          <div className="det-h2">DB 재구성 → sLLM 호출 → 결과 저장</div>
          {[
            {n:'01', title:'fetch_consultation_from_db(user_id, consultation_idx)', desc:'Supabase DB의 Consulting·AlgorithmStep·DetailElement 테이블을 JOIN하여 상담 전체 내용을 재구성합니다. 문제점·해결수단·차별성·효과·알고리즘 단계를 포함한 텍스트 요약을 생성합니다.'},
            {n:'02', title:'RunPod FastAPI 호출 — POST /generate-claims', desc:'재구성된 상담 텍스트를 RunPod 서버의 /generate-claims 엔드포인트로 POST 전송합니다. 서버에서 EXAONE sLLM이 독립항 1개와 종속항 2~4개를 생성하여 반환합니다.'},
            {n:'03', title:'save_claims_to_db()', desc:'생성된 청구항을 GeneratedClaim 테이블에 저장합니다. claim_1(독립항 전문)과 dependent_claims(종속항 리스트)를 분리 저장합니다.'},
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>

        <div className="det-section">
          <div className="det-kicker">RUNPOD SERVER — agents/runpod/main.py</div>
          <div className="det-h2">EXAONE 모델 로딩 및 추론</div>
          <div className="det-p">RunPod GPU 인스턴스에서 실행되는 FastAPI 서버입니다. 서버 시작 시 EXAONE 모델을 로딩하고 LoRA 어댑터를 적용합니다.</div>
          <div className="det-code">
            BASE_MODEL_NAME = "LGAI-EXAONE/EXAONE-3.0-7.8B-Instruct"<br/>
            LORA_HF_REPO = os.getenv("LORA_HF_REPO", "silverstone1004/claim")<br/><br/>
            # FastAPI 엔드포인트<br/>
            POST /generate-claims  # 청구항 생성<br/>
            GET  /health           # 서버 상태 확인<br/><br/>
            # Fallback — sLLM 미연결 시<br/>
            openai_client.chat.completions.create(model="gpt-4o", ...)
          </div>
          <div className="det-p">서버 헬스체크 URL은 환경변수 <code style={{background:'#F0EDE8',padding:'1px 6px'}}>CLAIM_BACKEND_URL</code>로 관리됩니다. 연결 실패 시 자동으로 GPT-4o로 fallback됩니다.</div>
        </div>

        <div className="det-section">
          <div className="det-kicker">EMBODIMENT AGENT — embodiment_agent.py</div>
          <div className="det-h2">발명의 설명 · 실시예 자동 생성</div>
          <div className="det-p"><code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>embodiment_agent.py</code>는 도면 생성 결과와 청구항을 결합하여 명세서의 "발명을 실시하기 위한 구체적인 내용" 섹션을 자동 작성합니다.</div>
          <div className="det-code">
            # 사용 모델<br/>
            MODEL_TEXT = "gpt-4o-mini" (temperature=0.2)<br/><br/>
            # 입력<br/>
            invention_output, claim_output, drawing_results(List[DrawingResult])<br/><br/>
            # 출력 JSON 구조<br/>
            {'{'}<br/>
            &nbsp;&nbsp;"brief_description_of_drawings": [<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;{'{'}"fig_number": "도 1", "description": "..."{'}'}<br/>
            &nbsp;&nbsp;],<br/>
            &nbsp;&nbsp;"embodiments": [<br/>
            &nbsp;&nbsp;&nbsp;&nbsp;{'{'}"fig_number": "도 1", "title": "...", "content": "..."{'}'}<br/>
            &nbsp;&nbsp;]<br/>
            {'}'}
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">FULL PIPELINE — patent_generation_pipeline.py</div>
          <div className="det-h2">최종 특허 문서 페이로드 생성</div>
          <div className="det-p"><code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>patent_generation_pipeline.py</code>의 <strong>run_full_pipeline()</strong>이 모든 에이전트를 순서대로 실행하여 최종 문서를 생성합니다.</div>
          <div className="det-code">
            1. generate_all_drawings()      # drawing_agent.py<br/>
            2. generate_and_save_embodiment_output()  # embodiment_agent.py<br/>
            3. build_patent_document_payload()  # 최종 통합<br/><br/>
            # 최종 출력: final_patent_document_payload.json<br/>
            {'{'}<br/>
            &nbsp;&nbsp;"invention_output": {'{}'},<br/>
            &nbsp;&nbsp;"claim_output": {'{}'},<br/>
            &nbsp;&nbsp;"drawings": [...],<br/>
            &nbsp;&nbsp;"brief_description_of_drawings": [...],<br/>
            &nbsp;&nbsp;"embodiments": [...]<br/>
            {'}'}
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            {q:'EXAONE sLLM을 선택한 이유는?', a:'LGAI가 개발한 EXAONE-3.0-7.8B-Instruct는 한국어 이해도가 높은 오픈소스 모델입니다. 한국 특허 데이터로 LoRA 파인튜닝을 적용하여 특허 청구항 형식과 법적 용어에 특화됐습니다.'},
            {q:'RunPod 서버가 꺼져있으면 어떻게 되나요?', a:'/health 엔드포인트로 상태를 확인하고, 연결 실패 시 자동으로 GPT-4o로 fallback됩니다. 환경변수 CLAIM_BACKEND_URL에 RunPod 서버 주소를 설정해야 합니다.'},
            {q:'독립항과 종속항은 어떻게 구분되나요?', a:'독립항(claim_1)은 발명의 핵심 기술적 특징을 독립적으로 기재한 가장 넓은 청구항입니다. 종속항(dependent_claims)은 독립항을 인용하여 추가 특징을 한정하며, 권리범위가 좁아지는 대신 등록 가능성이 높아집니다.'},
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>

        <div style={{display:'flex',gap:'1rem',flexWrap:'wrap'}}>
          <Link href="/service/drawing" style={{display:'inline-block',padding:'.85rem 2rem',background:'#111128',border:'1px solid #111128',color:'#C9A84C',fontSize:'.8rem',fontWeight:700}}>다음: 도면 생성 →</Link>
          <Link href="/contact" style={{display:'inline-block',padding:'.85rem 2rem',border:'1px solid #E8E4DC',color:'#444',fontSize:'.8rem'}}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
