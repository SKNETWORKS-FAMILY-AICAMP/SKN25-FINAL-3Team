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
        <div className="tag">02 — PRIOR ART SEARCH</div>
        <h1>선행기술 조사 에이전트</h1>
        <p>text-embedding-3-small + BM25 하이브리드 검색으로 KIPRIS 특허 코퍼스를 탐색합니다.</p>
      </div>

      <div className="det-wrap">

        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">prior_art_agent.py 기반 벡터+키워드 하이브리드 검색</div>
          <div className="det-p">
            <code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>agents/consultation/prior_art_agent.py</code>에서 구현됩니다. OpenAI <strong>text-embedding-3-small</strong>(1536차원)으로 특허 텍스트를 벡터화하고, BM25 키워드 검색과 RRF 알고리즘으로 결합하여 관련도 높은 선행기술을 탐색합니다.
          </div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">임베딩 모델</div><div className="det-cell-value">text-embedding-3-small (1536차원 벡터)</div></div>
            <div className="det-cell"><div className="det-cell-label">분석 모델</div><div className="det-cell-value">gpt-4o (ANALYZE_MODEL) — 유사도 결과 분석</div></div>
            <div className="det-cell"><div className="det-cell-label">검색 IPC 코드</div><div className="det-cell-value">G06F · G06N · G06Q · G06V (AI/SW 특허)</div></div>
            <div className="det-cell"><div className="det-cell-label">특허 DB</div><div className="det-cell-value">Supabase PatentCorpus 테이블 (로컬 코퍼스)</div></div>
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">HOW IT WORKS</div>
          <div className="det-h2">5단계 처리 파이프라인</div>
          {[
            {n:'01', title:'특허 코퍼스 로딩 — load_patent_corpus() / load_corpus_from_db()', desc:'G06F·G06N·G06Q·G06V 폴더의 특허 TXT 파일을 파싱하거나 Supabase PatentCorpus 테이블에서 로딩합니다. _parse_patent_txt()로 출원번호·제목·청구항·요약을 구조화합니다.'},
            {n:'02', title:'배치 임베딩 생성 — _embed_texts()', desc:'OpenAI text-embedding-3-small 모델로 발명 텍스트와 특허 코퍼스 청구항을 벡터화합니다. 배치당 최대 100개씩 처리하여 API 제한을 준수합니다. 1536차원 float 배열로 저장됩니다.'},
            {n:'03', title:'코사인 유사도 계산 — compare_claims()', desc:'발명 임베딩 벡터와 코퍼스 내 각 특허 청구항 벡터의 코사인 유사도를 계산합니다. 0~1 범위의 점수로 관련도를 수치화합니다.'},
            {n:'04', title:'RRF 하이브리드 검색', desc:'벡터 유사도 검색(시맨틱)과 BM25 키워드 검색을 Reciprocal Rank Fusion 알고리즘으로 결합합니다. 두 방식의 순위를 통합하여 최종 관련도 순으로 재랭킹합니다.'},
            {n:'05', title:'신규성·진보성 판정 및 리포트 생성', desc:'유사도 0.9↑ → 신규성 위협, 0.7~0.9 → 진보성 검토 필요, 0.5 미만 → 출원 가능으로 판정합니다. gpt-4o로 차별화 분석을 생성하고 {is_novel, top_similarity, top_patent, all_results, differentiation_analysis} 구조로 반환합니다.'},
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>

        <div className="det-section">
          <div className="det-kicker">DB SCHEMA</div>
          <div className="det-h2">PatentCorpus 테이블 구조</div>
          <div className="det-p"><code style={{background:'#F0EDE8',padding:'1px 6px',fontSize:'.82rem'}}>patent_db.py</code>의 PatentCorpus SQLAlchemy 모델로 정의됩니다.</div>
          <div className="det-code">
            PatentCorpus 컬럼:<br/>
            patent_number, title, applicant<br/>
            abstract, claims, description, raw_text<br/>
            ipc_class, file_name, file_path_key<br/>
            embedding  # JSON list[float] — 1536차원
          </div>
          <div className="det-p">DB 연결은 Supabase 환경변수(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)를 자동으로 조합하여 PostgreSQL URL을 구성합니다.</div>
        </div>

        <div className="det-section">
          <div className="det-kicker">OUTPUT</div>
          <div className="det-h2">반환 구조</div>
          <div className="det-code">
            {'{'}<br/>
            &nbsp;&nbsp;"is_novel": True/False,<br/>
            &nbsp;&nbsp;"top_similarity": 0.82,  # 최고 유사도<br/>
            &nbsp;&nbsp;"top_patent": {'{'}"app_num": "10-2023-...", "title": "...", "claim": "..."{'}'} ,<br/>
            &nbsp;&nbsp;"all_results": [...],     # 전체 유사 특허 리스트<br/>
            &nbsp;&nbsp;"differentiation_analysis": "..."  # gpt-4o 차별화 분석<br/>
            {'}'}
          </div>
        </div>

        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            {q:'RRF(Reciprocal Rank Fusion)이 왜 필요한가요?', a:'벡터 검색만으로는 키워드가 다른 동의어 기술을 놓칠 수 있고, BM25만으로는 의미적으로 유사하지만 단어가 다른 특허를 놓칩니다. RRF는 두 방식의 순위를 역수로 변환하여 합산함으로써 각 방식의 약점을 보완합니다.'},
            {q:'IPC 코드를 G06F·G06N·G06Q·G06V만 사용하는 이유는?', a:'현재 PatentAI는 AI·소프트웨어·컴퓨팅 분야(G06계열)에 특화되어 있습니다. 이 4개 코드가 한국 AI 특허의 90% 이상을 커버합니다. 향후 다른 기술 분야로 확장 예정입니다.'},
            {q:'코퍼스를 어떻게 구축했나요?', a:'load_corpus.py 스크립트로 KIPRIS에서 수집한 특허 TXT 파일을 파싱하여 PatentCorpus DB에 적재했습니다. 각 특허의 청구항을 text-embedding-3-small로 사전 임베딩하여 저장합니다.'},
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>

        <div style={{display:'flex',gap:'1rem',flexWrap:'wrap'}}>
          <Link href="/service/specification" style={{display:'inline-block',padding:'.85rem 2rem',background:'#111128',border:'1px solid #111128',color:'#C9A84C',fontSize:'.8rem',fontWeight:700}}>다음: 명세서 작성 →</Link>
          <Link href="/contact" style={{display:'inline-block',padding:'.85rem 2rem',border:'1px solid #E8E4DC',color:'#444',fontSize:'.8rem'}}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
