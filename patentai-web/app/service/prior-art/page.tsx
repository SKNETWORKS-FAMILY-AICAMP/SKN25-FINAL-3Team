'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export default function Page() {
  return (
    <div className="site">
      <style>{`
        .det-section{margin-bottom:3rem;padding-bottom:3rem;border-bottom:1px solid #E8E4DC;}
        .det-kicker{font-size:.65rem;font-weight:700;letter-spacing:.3em;color:#C9A84C;margin-bottom:.6rem;}
        .det-h2{font-family:'Noto Serif KR',serif;font-size:1.6rem;font-weight:300;color:#0A0A16;margin-bottom:1rem;}
        .det-p{font-size:.9rem;color:#444;line-height:2;word-break:keep-all;margin-bottom:1rem;}
        .det-list{list-style:none;padding:0;display:flex;flex-direction:column;gap:.5rem;margin-bottom:1.2rem;}
        .det-list li{display:flex;gap:.7rem;font-size:.88rem;color:#333;line-height:1.7;}
        .det-list li::before{content:'—';color:#C9A84C;flex-shrink:0;}
        .det-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:#E0DDD8;margin:1.2rem 0;}
        .det-cell{background:white;padding:1.2rem;}
        .det-cell-label{font-size:.62rem;font-weight:700;letter-spacing:.15em;color:#C9A84C;margin-bottom:.3rem;}
        .det-cell-value{font-size:.86rem;color:#222;line-height:1.7;word-break:keep-all;}
        .det-step{display:flex;gap:1rem;margin-bottom:1rem;}
        .det-step-num{width:34px;height:34px;border:1px solid rgba(201,168,76,.3);display:flex;align-items:center;justify-content:center;font-family:'Noto Serif KR',serif;color:#C9A84C;font-size:.78rem;flex-shrink:0;}
        .det-step-title{font-weight:700;font-size:.88rem;color:#0A0A16;margin-bottom:.3rem;}
        .det-step-desc{font-size:.83rem;color:#555;line-height:1.8;word-break:keep-all;}
        .qa-item{border:1px solid #E8E4DC;margin-bottom:.5rem;}
        .qa-q{font-size:.88rem;font-weight:700;color:#0A0A16;padding:1rem 1.2rem;}
        .qa-a{font-size:.83rem;color:#555;line-height:1.85;padding:.2rem 1.2rem 1rem;word-break:keep-all;}
        @media(max-width:900px){.det-grid{grid-template-columns:1fr;}}
      `}</style>
      <Nav />
      <div className="hero">
        <div className="tag">02 — PRIOR ART SEARCH</div>
        <h1>선행기술 조사<br/>에이전트</h1>
        <p>KIPRIS·USPTO·EPO 전 세계 특허 DB를 벡터 유사도 검색으로 탐색하여 신규성·진보성 위험을 사전에 파악합니다.</p>
      </div>
      <div style={{ padding:'3.5rem 6rem', maxWidth:900, margin:'0 auto' }}>
        <div className="det-section">
          <div className="det-kicker">OVERVIEW</div>
          <div className="det-h2">선행기술 조사란?</div>
          <div className="det-p">선행기술 조사는 특허 출원 전 동일·유사 기술이 이미 등록되어 있는지 확인하는 핵심 단계입니다. PatentAI는 단순 키워드 검색이 아닌 임베딩 벡터 유사도 + BM25 키워드 하이브리드 검색(RRF)으로 더 정확한 관련 특허를 탐색합니다.</div>
          <div className="det-grid">
            <div className="det-cell"><div className="det-cell-label">검색 DB</div><div className="det-cell-value">KIPRIS(한국)·USPTO(미국)·EPO(유럽)·JPO(일본)</div></div>
            <div className="det-cell"><div className="det-cell-label">검색 방식</div><div className="det-cell-value">벡터 유사도 + BM25 하이브리드 (RRF)</div></div>
            <div className="det-cell"><div className="det-cell-label">처리 시간</div><div className="det-cell-value">2–5분 (IPC 코드 4개 기준)</div></div>
            <div className="det-cell"><div className="det-cell-label">출력</div><div className="det-cell-value">유사도 점수 0~1 · 위험도 등급 · TOP-N 리스트</div></div>
          </div>
        </div>
        <div className="det-section">
          <div className="det-kicker">HOW IT WORKS</div>
          <div className="det-h2">동작 원리</div>
          {[
            { n:'01', title:'키워드·IPC 코드 자동 생성', desc:'상담 에이전트의 발명 구조화 데이터에서 핵심 기술 키워드를 추출하고, GPT-4o로 관련 IPC 분류 코드(G06F, G06N, G06Q, G06V 등)를 자동 생성합니다.' },
            { n:'02', title:'KIPRIS API 대량 수집', desc:'KIPRIS OpenAPI를 통해 IPC 코드별로 최근 10년 이내 특허를 대량 수집합니다. 수집된 특허 데이터는 출원번호·제목·청구항·요약 정보를 포함합니다.' },
            { n:'03', title:'임베딩 벡터 생성', desc:'OpenAI text-embedding-3-small 모델로 발명 텍스트와 수집된 특허 청구항을 벡터화합니다. 동일 차원의 임베딩 공간에서 코사인 유사도를 계산합니다.' },
            { n:'04', title:'하이브리드 검색 (RRF)', desc:'벡터 유사도 검색 결과와 BM25 키워드 검색 결과를 RRF(Reciprocal Rank Fusion) 알고리즘으로 결합합니다. 두 검색 방식의 장점을 살려 관련도가 높은 순으로 재랭킹합니다.' },
            { n:'05', title:'위험도 분석 및 리포트 생성', desc:'유사도 0.9 이상은 신규성 위협, 0.7~0.9는 진보성 위협으로 분류합니다. 유사 특허 TOP-N 목록, 위험도 등급, 출원 전략 권고사항을 포함한 리포트를 생성합니다.' },
          ].map(s => (
            <div key={s.n} className="det-step">
              <div className="det-step-num">{s.n}</div>
              <div><div className="det-step-title">{s.title}</div><div className="det-step-desc">{s.desc}</div></div>
            </div>
          ))}
        </div>
        <div className="det-section">
          <div className="det-kicker">FAQ</div>
          <div className="det-h2">자주 묻는 질문</div>
          {[
            { q:'벡터 검색이 키워드 검색보다 왜 더 좋은가요?', a:'키워드 검색은 정확히 같은 단어가 있어야 결과가 나옵니다. 벡터 검색은 의미적으로 유사한 특허도 탐색할 수 있어 키워드가 다르더라도 동일 기술 분야의 선행기술을 발견할 수 있습니다.' },
            { q:'해외 특허도 조사하나요?', a:'현재 KIPRIS(한국) 기반으로 IPC 코드 검색을 수행합니다. USPTO·EPO 직접 연동은 순차적으로 확대 예정입니다. Google Patents 링크를 통한 수동 조회도 함께 제공합니다.' },
            { q:'유사도 점수 해석 기준이 있나요?', a:'0.9 이상: 신규성 위협 높음, 0.7~0.9: 진보성 검토 필요, 0.5~0.7: 차별점 확보 가능, 0.5 미만: 출원 가능 수준으로 판단합니다.' },
          ].map((item, i) => (
            <div key={i} className="qa-item">
              <div className="qa-q">Q. {item.q}</div>
              <div className="qa-a">A. {item.a}</div>
            </div>
          ))}
        </div>
        <div style={{ display:'flex', gap:'1rem' }}>
          <Link href="/service/specification" style={{ display:'inline-block', padding:'.85rem 2rem', background:'#111128', border:'1px solid #111128', color:'#C9A84C', fontSize:'.8rem', fontWeight:700 }}>다음: 명세서 작성 →</Link>
          <Link href="/contact" style={{ display:'inline-block', padding:'.85rem 2rem', border:'1px solid #E8E4DC', color:'#444', fontSize:'.8rem' }}>상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
