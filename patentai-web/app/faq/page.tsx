'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const faqs = [
  {
    category: '특허 출원',
    items: [
      {
        q: '특허 출원까지 얼마나 걸리나요?',
        a: '출원서 작성부터 특허청 접수까지 보통 2~4주가 소요됩니다. PatentAI를 이용하면 명세서 초안 작성 시간을 대폭 단축할 수 있습니다. 심사 및 등록까지는 평균 14~18개월이 소요됩니다.',
      },
      {
        q: '특허 출원 비용은 어떻게 되나요?',
        a: '특허청 관납료(출원료 약 46,000원~)와 변리사 수수료(평균 100~300만원)로 구성됩니다. PatentAI는 AI 자동화를 통해 명세서 작성 비용을 절감해 드립니다. 상담 신청 후 정확한 견적을 안내드립니다.',
      },
      {
        q: '해외 특허도 출원할 수 있나요?',
        a: 'PCT(국제특허협력조약)를 통해 160개국 이상에 동시 출원이 가능합니다. 미국(USPTO), 유럽(EPO), 일본(JPO), 중국(CNIPA) 등 주요국 출원도 지원합니다.',
      },
    ],
  },
  {
    category: 'PatentAI 서비스',
    items: [
      {
        q: 'PatentAI는 어떤 서비스인가요?',
        a: 'PatentAI는 AI 기반 지식재산 상담 시스템으로, 발명 상담→선행기술 조사→명세서 작성→도면 생성→심사 대응까지 특허 출원 전 과정을 자동화합니다. 변리사의 전문 업무를 AI로 보조하여 시간과 비용을 절감합니다.',
      },
      {
        q: 'AI가 작성한 명세서를 바로 출원에 사용할 수 있나요?',
        a: 'PatentAI가 생성하는 문서는 고품질 초안입니다. 전문 변리사의 최종 검토 후 출원하는 것을 권장합니다. AI 초안을 활용하면 변리사 작업 시간이 크게 단축되어 전체 비용이 절감됩니다.',
      },
      {
        q: '도면은 어떤 형식으로 제공되나요?',
        a: 'SVG(벡터) 및 PNG(고해상도 래스터) 형식으로 제공됩니다. 특허청 제출 기준에 맞는 흑백 선화 스타일로 생성되며, 블록도·흐름도·시퀀스 다이어그램 등을 지원합니다.',
      },
      {
        q: '상담 내용은 안전하게 보호되나요?',
        a: '모든 상담 내용은 암호화되어 저장되며, 제3자에게 공유되지 않습니다. 발명 내용의 기밀성은 엄격히 보장됩니다.',
      },
    ],
  },
  {
    category: '선행기술 조사',
    items: [
      {
        q: '선행기술 조사가 왜 중요한가요?',
        a: '선행기술 조사를 통해 동일하거나 유사한 기술이 이미 특허로 등록되어 있는지 확인합니다. 이를 통해 출원 전략을 수립하고, 특허 거절 위험을 미리 파악할 수 있습니다.',
      },
      {
        q: '어떤 데이터베이스를 활용하나요?',
        a: 'KIPRIS(한국), USPTO(미국), EPO(유럽), JPO(일본) 등 주요국 특허 데이터베이스를 활용합니다. 벡터 유사도 기반 AI 검색으로 키워드 검색보다 더 관련성 높은 결과를 제공합니다.',
      },
    ],
  },
  {
    category: '이용 방법',
    items: [
      {
        q: '어떻게 시작하면 되나요?',
        a: '상담 신청 페이지에서 발명 내용을 간단히 기재해 주시면, 담당자가 1~2 영업일 내 연락드립니다. 또는 AI 상담 도우미(오른쪽 하단 버튼)를 통해 즉시 질문하실 수 있습니다.',
      },
      {
        q: '비기술자도 이용할 수 있나요?',
        a: '네, 기술적 배경이 없어도 발명 아이디어만 있으면 충분합니다. PatentAI의 상담 에이전트가 단계별 질문을 통해 발명 내용을 체계적으로 정리해 드립니다.',
      },
    ],
  },
]

export default function FaqPage() {
  const [openIdx, setOpenIdx] = useState<string | null>(null)

  return (
    <div className="site">
      <style>{`
        .faq-category { margin-bottom: 2.5rem; }
        .faq-category-title {
          font-family: 'Noto Serif KR', serif;
          font-size: 1.1rem; font-weight: 500;
          color: #111128; margin-bottom: 1rem;
          padding-bottom: 0.6rem;
          border-bottom: 2px solid #C9A84C;
          display: inline-block;
        }
        .faq-item { border: 1px solid #E8E4DC; margin-bottom: 0.5rem; background: white; }
        .faq-q {
          width: 100%; text-align: left; background: none; border: none;
          padding: 1.1rem 1.4rem; cursor: pointer;
          display: flex; justify-content: space-between; align-items: center;
          font-size: 0.92rem; font-weight: 600; color: #111128;
          font-family: inherit; transition: background 0.15s;
        }
        .faq-q:hover { background: #FAFAF8; }
        .faq-q.open { color: #C9A84C; background: #FAFAF8; }
        .faq-icon { color: #C9A84C; font-size: 1.1rem; flex-shrink: 0; margin-left: 1rem; transition: transform 0.2s; }
        .faq-icon.open { transform: rotate(45deg); }
        .faq-a {
          padding: 0 1.4rem 1.2rem;
          font-size: 0.88rem; line-height: 1.8; color: #555;
          border-top: 1px solid #F0EDE8;
          animation: fadeIn 0.18s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        .faq-cta {
          background: #111128; padding: 3rem; text-align: center; margin-top: 3rem;
        }
        .faq-cta-title { font-family: 'Noto Serif KR', serif; font-size: 1.6rem; font-weight: 300; color: #F0EDE6; margin-bottom: 0.6rem; }
        .faq-cta-sub { color: #9999B8; font-size: 0.9rem; margin-bottom: 1.5rem; }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">FAQ</div>
        <h1>자주 묻는 질문</h1>
        <p>특허 출원과 PatentAI 서비스에 대해 가장 많이 묻는 질문들을 정리했습니다.</p>
      </div>

      <div className="section" style={{ maxWidth: 860, margin: '0 auto' }}>
        <div className="line"></div>
        <div className="title">FAQ</div>

        {faqs.map(cat => (
          <div className="faq-category" key={cat.category}>
            <div className="faq-category-title">{cat.category}</div>
            {cat.items.map((item, i) => {
              const key = `${cat.category}-${i}`
              const isOpen = openIdx === key
              return (
                <div className="faq-item" key={key}>
                  <button className={`faq-q ${isOpen ? 'open' : ''}`} onClick={() => setOpenIdx(isOpen ? null : key)}>
                    <span>Q. {item.q}</span>
                    <span className={`faq-icon ${isOpen ? 'open' : ''}`}>+</span>
                  </button>
                  {isOpen && <div className="faq-a">A. {item.a}</div>}
                </div>
              )
            })}
          </div>
        ))}

        <div className="faq-cta">
          <div className="faq-cta-title">더 궁금한 점이 있으신가요?</div>
          <div className="faq-cta-sub">전문 상담팀이 빠르게 답변드립니다.</div>
          <Link href="/contact" style={{
            display: 'inline-block', padding: '0.85rem 2.5rem',
            border: '1px solid #C9A84C', color: '#C9A84C',
            fontSize: '0.88rem', fontWeight: 700, letterSpacing: '0.08em', textDecoration: 'none',
            transition: '0.2s',
          }}>상담 신청하기 →</Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
