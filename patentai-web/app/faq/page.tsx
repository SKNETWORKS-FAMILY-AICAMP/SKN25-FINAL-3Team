'use client'

import { useState, useMemo } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const categories = [
  { id: 'all',      label: '전체',           icon: '◈' },
  { id: 'filing',   label: '특허 출원',       icon: '📋' },
  { id: 'service',  label: 'PatentAI 서비스', icon: '🤖' },
  { id: 'priorart', label: '선행기술 조사',   icon: '🔍' },
  { id: 'spec',     label: '명세서 · 청구항', icon: '📝' },
  { id: 'drawing',  label: '도면 생성',       icon: '🎨' },
  { id: 'cost',     label: '비용 · 기간',     icon: '💼' },
  { id: 'usage',    label: '이용 방법',       icon: '💡' },
]

const faqs = [
  // 특허 출원
  {
    cat: 'filing',
    q: '특허 출원이란 무엇인가요?',
    a: '특허 출원은 발명자가 특허청에 발명의 보호를 요청하는 절차입니다. 출원서, 명세서(청구항·발명의 설명·도면)를 작성하여 특허청에 제출하면 심사를 거쳐 등록 여부가 결정됩니다. 출원일부터 20년간 독점적 실시권이 부여됩니다.',
    ref: '특허법 제42조',
  },
  {
    cat: 'filing',
    q: '출원서 작성부터 접수까지 얼마나 걸리나요?',
    a: '일반적으로 2~4주가 소요됩니다. PatentAI를 이용하면 명세서 초안을 수 시간 내 생성할 수 있어 전체 준비 기간을 대폭 단축할 수 있습니다. 특허청 심사 및 등록까지는 통상 14~18개월이 소요됩니다.',
    ref: '특허청 심사처리기간 기준',
  },
  {
    cat: 'filing',
    q: '해외 특허 출원은 어떻게 하나요?',
    a: 'PCT(특허협력조약) 국제출원을 통해 1건의 출원으로 160개국 이상에서 동시 보호를 받을 수 있습니다. 우선일로부터 30개월 내에 각국에 진입할 수 있으며, 미국(USPTO)·유럽(EPO)·일본(JPO)·중국(CNIPA) 직접 출원도 지원합니다.',
    ref: 'PCT 국제조약',
  },
  {
    cat: 'filing',
    q: '우선권 주장이란 무엇인가요?',
    a: '파리 협약에 따라 국내 최초 출원일로부터 12개월 내에 해외 출원 시 국내 출원일을 해외 출원일로 인정받는 제도입니다. 이를 통해 해외 출원 준비 기간을 확보하면서도 신규성을 유지할 수 있습니다.',
    ref: '파리 협약 제4조',
  },
  // PatentAI 서비스
  {
    cat: 'service',
    q: 'PatentAI는 어떤 서비스인가요?',
    a: 'PatentAI는 AI 기반 지식재산 상담 시스템으로, ① 발명 상담 구조화 → ② 선행기술 조사 → ③ 명세서·청구항 작성 → ④ 특허 도면 자동 생성 → ⑤ 심사 대응까지 특허 출원 전 과정을 AI로 자동화합니다. 변리사의 핵심 업무를 AI가 보조하여 시간과 비용을 대폭 절감합니다.',
    ref: null,
  },
  {
    cat: 'service',
    q: 'AI가 작성한 명세서를 바로 출원에 사용할 수 있나요?',
    a: 'PatentAI가 생성하는 명세서는 고품질 초안입니다. 특허청 제출 전 전문 변리사의 최종 검토를 권장합니다. AI 초안을 활용하면 변리사 작업 시간이 60~80% 단축되어 전체 비용이 절감됩니다.',
    ref: null,
  },
  {
    cat: 'service',
    q: '상담 내용과 발명 정보는 어떻게 보호되나요?',
    a: '모든 상담 내용은 AES-256 암호화를 적용하여 저장됩니다. 제3자와의 정보 공유는 일절 없으며, 개인정보보호법 및 영업비밀보호법에 따라 발명 내용의 기밀성을 엄격히 보장합니다.',
    ref: '개인정보보호법 제24조',
  },
  {
    cat: 'service',
    q: '서비스 이용에 전문 지식이 필요한가요?',
    a: '전혀 필요하지 않습니다. 발명 아이디어만 있으면 충분합니다. PatentAI의 상담 에이전트가 단계별 질문을 통해 발명의 문제점·해결수단·효과·구성요소를 체계적으로 정리해 드립니다.',
    ref: null,
  },
  // 선행기술 조사
  {
    cat: 'priorart',
    q: '선행기술 조사가 왜 중요한가요?',
    a: '선행기술 조사는 동일·유사 기술의 기존 특허 존재 여부를 사전에 파악하는 핵심 단계입니다. 조사 없이 출원하면 신규성·진보성 결여로 거절될 위험이 높으며, 등록 후에도 무효심판 위험이 있습니다. 조사 결과를 바탕으로 권리범위를 차별화하는 출원 전략을 수립할 수 있습니다.',
    ref: '특허법 제29조(신규성·진보성)',
  },
  {
    cat: 'priorart',
    q: '어떤 데이터베이스를 활용하나요?',
    a: 'KIPRIS(한국 특허청), USPTO(미국), EPO(유럽), JPO(일본), CNIPA(중국) 등 주요국 특허 DB를 활용합니다. PatentAI는 단순 키워드 검색이 아닌 임베딩 벡터 유사도 + 키워드 하이브리드 검색으로 더 정확한 관련 특허를 탐색합니다.',
    ref: 'KIPRIS, USPTO, EPO Espacenet',
  },
  {
    cat: 'priorart',
    q: '조사 결과 보고서는 어떻게 제공되나요?',
    a: '유사도 점수(0~1), 유사 특허 TOP-N 목록, 신규성·진보성 위험도 등급, 출원 전략 권고사항이 포함된 리포트를 제공합니다. 각 유사 특허의 청구항 비교표도 함께 제공됩니다.',
    ref: null,
  },
  // 명세서 · 청구항
  {
    cat: 'spec',
    q: '청구항 작성 시 가장 중요한 것은 무엇인가요?',
    a: '청구항은 특허권의 보호범위를 결정하는 가장 중요한 부분입니다. 권리범위가 너무 넓으면 신규성·진보성 문제로 거절되고, 너무 좁으면 경쟁사가 쉽게 회피할 수 있습니다. PatentAI는 선행기술 조사 결과를 반영하여 적절한 권리범위의 독립항·종속항을 자동 생성합니다.',
    ref: '특허법 제42조 제4항',
  },
  {
    cat: 'spec',
    q: '명세서에는 어떤 내용이 포함되어야 하나요?',
    a: '특허 명세서는 ① 발명의 명칭 ② 기술분야 ③ 배경기술 ④ 발명의 내용(과제·해결수단·효과) ⑤ 도면의 간단한 설명 ⑥ 발명을 실시하기 위한 구체적인 내용 ⑦ 청구범위 ⑧ 도면으로 구성됩니다. PatentAI는 상담 내용을 바탕으로 각 항목을 자동 초안화합니다.',
    ref: '특허법 제42조 제2항',
  },
  // 도면 생성
  {
    cat: 'drawing',
    q: '특허 도면은 어떤 기준을 충족해야 하나요?',
    a: '특허청 도면 기준에 따라 흑백 선화로 작성해야 하며, 도면부호(참조번호)를 명시해야 합니다. 도면의 크기·여백·선 굵기 등 형식 요건도 충족해야 합니다. PatentAI는 이러한 특허청 실무 기준을 자동으로 반영하여 SVG/PNG 도면을 생성합니다.',
    ref: '특허법 시행규칙 별지 제15호',
  },
  {
    cat: 'drawing',
    q: '어떤 종류의 도면을 생성할 수 있나요?',
    a: '블록도(시스템 구성), 흐름도(알고리즘·절차), 시퀀스 다이어그램(통신·상호작용), 상태도(상태 전이), UI 화면도 등 5가지 유형을 지원합니다. 명세서 텍스트를 분석하여 적합한 도면 유형을 자동 판별합니다.',
    ref: null,
  },
  {
    cat: 'drawing',
    q: '도면 품질은 어떻게 보장되나요?',
    a: '생성된 도면에 대해 ① 도면부호 완비 여부 ② 구성요소 충족 여부 ③ 렌더링 품질을 자동 검증하여 100점 만점의 품질 점수와 A~D 등급을 산출합니다. 75점 미만 도면은 자동 보정 과정을 거칩니다.',
    ref: null,
  },
  // 비용 · 기간
  {
    cat: 'cost',
    q: '특허 출원 관련 비용은 어떻게 되나요?',
    a: '크게 ① 특허청 관납료(출원료 56,000원~, 심사청구료 143,000원~/청구항)와 ② 변리사 수수료(평균 150~350만원)로 구성됩니다. PatentAI AI 서비스 이용 시 명세서 초안 비용을 절감하여 전체 비용을 20~40% 줄일 수 있습니다.',
    ref: '특허법 시행규칙 별표 3 관납료',
  },
  {
    cat: 'cost',
    q: '심사청구는 언제까지 해야 하나요?',
    a: '출원일로부터 3년 이내에 심사청구를 하지 않으면 출원이 취하된 것으로 간주됩니다. 조기 심사청구(우선심사)를 이용하면 평균 2~5개월 내에 심사결과를 받을 수 있으며, 벤처기업·중소기업·녹색기술 등은 우선심사 대상입니다.',
    ref: '특허법 제59조',
  },
  // 이용 방법
  {
    cat: 'usage',
    q: '어떻게 시작하면 되나요?',
    a: '① 우측 하단 AI 상담 도우미로 즉시 질문 ② 상담 신청 페이지에서 발명 내용 작성 후 접수 두 가지 방법으로 시작할 수 있습니다. 상담 신청 후 영업일 기준 1~2일 내 전담 담당자가 연락드립니다.',
    ref: null,
  },
  {
    cat: 'usage',
    q: '스타트업·개인 발명가도 이용할 수 있나요?',
    a: '네, PatentAI는 대기업부터 스타트업·개인 발명가까지 모두 이용 가능합니다. 특히 특허 전담 부서가 없는 스타트업과 비용이 부담되는 개인 발명가에게 AI 자동화로 시간과 비용을 절감할 수 있어 더욱 유용합니다.',
    ref: null,
  },
]

export default function FaqPage() {
  const [activeTab, setActiveTab] = useState('all')
  const [openIdx, setOpenIdx]     = useState<number | null>(null)
  const [search, setSearch]       = useState('')

  const filtered = useMemo(() => {
    return faqs.filter(f => {
      const matchCat    = activeTab === 'all' || f.cat === activeTab
      const matchSearch = !search || f.q.includes(search) || f.a.includes(search)
      return matchCat && matchSearch
    })
  }, [activeTab, search])

  return (
    <div className="site">
      <style>{`
        .faq-stats {
          background: #111128; display: flex; justify-content: center;
          gap: 4rem; padding: 1.4rem 2rem;
          border-bottom: 1px solid rgba(201,168,76,0.2);
        }
        .faq-stat-item { text-align: center; }
        .faq-stat-num { color: #C9A84C; font-family: 'Noto Serif KR',serif; font-size: 1.5rem; font-weight: 300; }
        .faq-stat-label { color: #7777A0; font-size: 0.74rem; margin-top: 2px; }

        .faq-search-wrap {
          background: #F5F4F1; padding: 2rem 5.5rem;
          border-bottom: 1px solid #E8E4DC;
        }
        .faq-search {
          max-width: 600px; margin: 0 auto;
          display: flex; align-items: center;
          background: white; border: 1px solid #D8D2C8;
          padding: 0 1.2rem; gap: 0.8rem;
          transition: border 0.2s;
        }
        .faq-search:focus-within { border-color: #C9A84C; box-shadow: 0 0 0 1px #C9A84C; }
        .faq-search input {
          flex: 1; border: none; outline: none; padding: 0.85rem 0;
          font-size: 0.9rem; font-family: inherit; background: transparent;
        }
        .faq-search-icon { color: #C9A84C; font-size: 1rem; flex-shrink: 0; }

        .faq-layout {
          display: grid; grid-template-columns: 220px 1fr; gap: 3rem;
          padding: 3rem 5.5rem; align-items: start;
        }

        .faq-sidebar { position: sticky; top: 2rem; }
        .faq-sidebar-title { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.2em; color: #C9A84C; margin-bottom: 0.8rem; }
        .faq-tab {
          display: flex; align-items: center; gap: 0.6rem;
          width: 100%; text-align: left; background: none; border: none;
          padding: 0.7rem 1rem; cursor: pointer; font-family: inherit;
          font-size: 0.86rem; color: #666; transition: 0.15s;
          border-left: 2px solid transparent;
        }
        .faq-tab:hover { color: #111128; background: #F5F4F1; }
        .faq-tab.active { color: #111128; font-weight: 700; border-left-color: #C9A84C; background: #F5F4F1; }
        .faq-tab-count {
          margin-left: auto; background: #E8E4DC; color: #888;
          font-size: 0.72rem; padding: 1px 7px; border-radius: 10px;
        }
        .faq-tab.active .faq-tab-count { background: #C9A84C; color: #111128; }

        .faq-content { min-width: 0; }
        .faq-count-label { font-size: 0.82rem; color: #999; margin-bottom: 1.2rem; }
        .faq-count-label strong { color: #C9A84C; }

        .faq-item {
          border: 1px solid #E8E4DC; margin-bottom: 0.6rem;
          background: white; transition: border-color 0.15s;
        }
        .faq-item:hover { border-color: rgba(201,168,76,0.4); }
        .faq-item.open { border-color: #C9A84C; }

        .faq-q {
          width: 100%; text-align: left; background: none; border: none;
          padding: 1.2rem 1.5rem; cursor: pointer;
          display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;
          font-size: 0.92rem; font-weight: 600; color: #111128;
          font-family: inherit;
        }
        .faq-q-left { display: flex; align-items: flex-start; gap: 0.8rem; }
        .faq-q-badge {
          background: #F0EDE6; color: #C9A84C; font-size: 0.72rem; font-weight: 700;
          padding: 2px 8px; border-radius: 10px; flex-shrink: 0; margin-top: 2px;
        }
        .faq-icon { color: #C9A84C; font-size: 1.3rem; flex-shrink: 0; transition: transform 0.22s; line-height: 1; }
        .faq-icon.open { transform: rotate(45deg); }

        .faq-a-wrap {
          border-top: 1px solid #F0EDE8;
          padding: 1.4rem 1.5rem 1.6rem 2rem;
          animation: fadeIn 0.18s ease;
          border-left: 3px solid #C9A84C;
          background: #FDFCFA;
        }
        .faq-a-label {
          font-size: 0.72rem; font-weight: 700; letter-spacing: 0.15em;
          color: #C9A84C; margin-bottom: 0.6rem;
        }
        .faq-a {
          font-size: 0.92rem; line-height: 2; color: #333;
          word-break: keep-all;
        }
        .faq-ref {
          display: inline-flex; align-items: center; gap: 0.4rem;
          margin-top: 1rem; color: #999; font-size: 0.76rem;
          border: 1px solid #E8E4DC; padding: 3px 10px; border-radius: 20px;
          background: white;
        }
        .faq-ref::before { content: '📌'; font-size: 0.72rem; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }

        .faq-empty { text-align: center; padding: 4rem 2rem; color: #aaa; font-size: 0.9rem; }

        .faq-cta-band {
          background: #111128; margin: 3rem 5.5rem;
          padding: 2.8rem 3rem; display: flex;
          align-items: center; justify-content: space-between; gap: 2rem;
          border-left: 4px solid #C9A84C;
        }
        .faq-cta-text-title { font-family: 'Noto Serif KR',serif; font-size: 1.4rem; font-weight: 300; color: #F0EDE6; margin-bottom: 0.3rem; }
        .faq-cta-text-sub { color: #7777A0; font-size: 0.86rem; }
        .faq-cta-btn {
          display: inline-block; padding: '0.85rem 2.2rem';
          border: '1px solid #C9A84C'; color: '#C9A84C';
          text-decoration: none; font-weight: 700;
          font-size: 0.88rem; letter-spacing: 0.08em;
          white-space: nowrap; flex-shrink: 0;
          transition: 0.2s;
        }

        @media (max-width: 900px) {
          .faq-layout { grid-template-columns: 1fr; padding: 2rem 1.5rem; }
          .faq-sidebar { position: static; display: flex; flex-wrap: wrap; gap: 0.4rem; }
          .faq-tab { width: auto; border-left: none; border: 1px solid #E8E4DC; border-radius: 20px; padding: 0.4rem 0.9rem; }
          .faq-tab.active { border-color: #C9A84C; }
          .faq-search-wrap { padding: 1.5rem; }
          .faq-cta-band { flex-direction: column; margin: 2rem 1.5rem; }
          .faq-stats { gap: 2rem; flex-wrap: wrap; }
        }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">FAQ</div>
        <h1>자주 묻는 질문</h1>
        <p>특허 출원과 PatentAI 서비스에 대해 전문적으로 답변드립니다.</p>
      </div>

      {/* 통계 바 */}
      <div className="faq-stats">
        {[
          { num: `${faqs.length}개`, label: '총 Q&A' },
          { num: `${categories.length - 1}개`, label: '카테고리' },
          { num: '1~2일', label: '평균 응답 기간' },
          { num: '98%', label: '고객 만족도' },
        ].map(s => (
          <div className="faq-stat-item" key={s.label}>
            <div className="faq-stat-num">{s.num}</div>
            <div className="faq-stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* 검색 */}
      <div className="faq-search-wrap">
        <div className="faq-search">
          <span className="faq-search-icon">🔍</span>
          <input
            placeholder="궁금한 내용을 검색하세요. 예: 출원 비용, 도면 형식…"
            value={search}
            onChange={e => { setSearch(e.target.value); setOpenIdx(null) }}
          />
          {search && <button onClick={() => setSearch('')} style={{ background: 'none', border: 'none', color: '#aaa', cursor: 'pointer', fontSize: '1.1rem' }}>×</button>}
        </div>
      </div>

      {/* 레이아웃 */}
      <div className="faq-layout">
        {/* 사이드바 */}
        <div className="faq-sidebar">
          <div className="faq-sidebar-title">CATEGORIES</div>
          {categories.map(cat => {
            const cnt = cat.id === 'all' ? faqs.length : faqs.filter(f => f.cat === cat.id).length
            return (
              <button
                key={cat.id}
                className={`faq-tab ${activeTab === cat.id ? 'active' : ''}`}
                onClick={() => { setActiveTab(cat.id); setOpenIdx(null) }}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
                <span className="faq-tab-count">{cnt}</span>
              </button>
            )
          })}
        </div>

        {/* FAQ 목록 */}
        <div className="faq-content">
          <div className="faq-count-label">
            <strong>{filtered.length}개</strong>의 질문이 있습니다.
          </div>

          {filtered.length === 0 && (
            <div className="faq-empty">검색 결과가 없습니다. 다른 키워드로 검색해보세요.</div>
          )}

          {filtered.map((item, i) => {
            const catLabel = categories.find(c => c.id === item.cat)?.label ?? ''
            const isOpen   = openIdx === i
            return (
              <div key={i} className={`faq-item ${isOpen ? 'open' : ''}`}>
                <button className="faq-q" onClick={() => setOpenIdx(isOpen ? null : i)}>
                  <div className="faq-q-left">
                    <span className="faq-q-badge">{catLabel}</span>
                    <span>{item.q}</span>
                  </div>
                  <span className={`faq-icon ${isOpen ? 'open' : ''}`}>+</span>
                </button>
                {isOpen && (
                  <div className="faq-a-wrap">
                    <div className="faq-a-label">ANSWER</div>
                    <div className="faq-a">{item.a}</div>
                    {item.ref && <div className="faq-ref">{item.ref}</div>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* CTA 배너 */}
      <div className="faq-cta-band">
        <div>
          <div className="faq-cta-text-title">더 궁금한 점이 있으신가요?</div>
          <div className="faq-cta-text-sub">전문 상담팀이 영업일 1~2일 내 빠르게 답변드립니다.</div>
        </div>
        <Link href="/contact" style={{
          display: 'inline-block', padding: '0.85rem 2.2rem',
          border: '1px solid #C9A84C', color: '#C9A84C',
          textDecoration: 'none', fontWeight: 700,
          fontSize: '0.88rem', letterSpacing: '0.08em', whiteSpace: 'nowrap',
        }}>
          상담 신청하기 →
        </Link>
      </div>

      <Footer />
    </div>
  )
}
