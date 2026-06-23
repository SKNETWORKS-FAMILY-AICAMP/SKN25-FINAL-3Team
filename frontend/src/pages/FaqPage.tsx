import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FAQ_CATEGORIES } from '../data/faqs'
import Reveal from '../components/Reveal'

export default function FaqPage() {
  const [activeFaqCategory, setActiveFaqCategory] = useState(0)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <div style={{ paddingTop: 70 }}>
      <section style={{ padding: '110px 0 0', textAlign: 'center', background: 'var(--lf-bg2)' }}>
        <div className="container">
          <Reveal variant="scale">
            <span className="label">FAQ</span>
            <h1 style={{ fontSize: 'clamp(32px,4vw,48px)', color: 'var(--lf-navy)', marginBottom: 16 }}>
              자주 묻는 <span className="text-gradient">질문</span>
            </h1>
            <p style={{ fontSize: 15.5, color: 'var(--lf-mid)', lineHeight: 1.9, maxWidth: 560, margin: '0 auto' }}>
              PYPI 사용 중 궁금한 점을 분야별로 모았습니다.
            </p>
          </Reveal>
        </div>
      </section>

      <section style={{ padding: '70px 0 150px' }}>
        <div className="container" style={{ maxWidth: 820 }}>
          <Reveal>
            <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 36 }}>
              {FAQ_CATEGORIES.map((cat, i) => {
                const isActive = activeFaqCategory === i
                return (
                  <button key={cat.category}
                    onClick={() => { setActiveFaqCategory(i); setOpenFaq(null) }}
                    style={{
                      fontSize: 12.5, fontWeight: 700, padding: '9px 18px', borderRadius: 999,
                      whiteSpace: 'nowrap', cursor: 'pointer', fontFamily: 'var(--lf-sans)',
                      border: isActive ? '1px solid var(--lf-dark)' : '1px solid var(--lf-border)',
                      background: isActive ? 'var(--lf-dark)' : 'var(--lf-bg2)',
                      color: isActive ? '#fff' : 'var(--lf-mid)',
                      transition: 'background .2s, color .2s, border-color .2s',
                    }}
                  >{cat.category}</button>
                )
              })}
            </div>
          </Reveal>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {FAQ_CATEGORIES[activeFaqCategory].items.map((item, i) => {
              const isOpen = openFaq === i
              return (
                <Reveal key={i} delay={i * 60} style={{ background: 'var(--lf-bg2)', borderRadius: 14, overflow: 'hidden' }}>
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%',
                      background: 'none', border: 'none', cursor: 'pointer', padding: '20px 24px',
                      fontFamily: 'var(--lf-sans)', textAlign: 'left',
                    }}
                  >
                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--lf-navy)' }}>{item.q}</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--lf-gold)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                      style={{ flexShrink: 0, marginLeft: 16, transition: 'transform .2s', transform: isOpen ? 'rotate(180deg)' : 'none' }}
                    ><path d="M6 9l6 6 6-6" /></svg>
                  </button>
                  {isOpen && (
                    <div style={{ padding: '0 24px 22px' }}>
                      {item.a.split('\n\n').map((para: string, j: number) => (
                        <p key={j} style={{ fontSize: 15, lineHeight: 2.05, color: 'var(--lf-mid)', marginTop: j > 0 ? 14 : 0 }}>{para}</p>
                      ))}
                    </div>
                  )}
                </Reveal>
              )
            })}
          </div>

          <div style={{ textAlign: 'center', marginTop: 56 }}>
            <Link to="/" className="btn-line">홈으로</Link>
          </div>
        </div>
      </section>
    </div>
  )
}