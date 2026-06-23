import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FAQ_CATEGORIES } from '../data/faqs'
import Reveal from './Reveal'

interface Props {
  id?: string
  showHeading?: boolean
  showHomeLink?: boolean
}

export default function FaqSection({ id, showHeading = false, showHomeLink = false }: Props) {
  const [activeCategory, setActiveCategory] = useState(0)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <section
      id={id}
      style={{
        padding: showHeading ? '130px 0' : '70px 0 150px',
        background: showHeading ? 'var(--lf-bg2)' : 'var(--lf-bg)',
        scrollMarginTop: 90,
      }}
    >
      <div className="container" style={{ maxWidth: 820 }}>
        {showHeading && (
          <Reveal variant="scale">
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
              <span className="label">FAQ</span>
              <h2 style={{ fontSize: 'clamp(28px,3vw,41px)', color: 'var(--lf-navy)', marginBottom: 14 }}>
                자주 묻는 질문
              </h2>
              <p style={{ fontSize: 15.5, color: 'var(--lf-mid)', lineHeight: 1.9 }}>
                PYPI 사용 중 궁금한 점을 분야별로 확인해보세요.
              </p>
            </div>
          </Reveal>
        )}

        <Reveal>
          <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 36 }}>
            {FAQ_CATEGORIES.map((category, index) => {
              const isActive = activeCategory === index
              return (
                <button
                  key={category.category}
                  type="button"
                  onClick={() => {
                    setActiveCategory(index)
                    setOpenFaq(null)
                  }}
                  style={{
                    fontSize: 12.5,
                    fontWeight: 700,
                    padding: '9px 18px',
                    borderRadius: 999,
                    whiteSpace: 'nowrap',
                    cursor: 'pointer',
                    fontFamily: 'var(--lf-sans)',
                    border: isActive ? '1px solid var(--lf-dark)' : '1px solid var(--lf-border)',
                    background: isActive ? 'var(--lf-dark)' : 'var(--lf-bg)',
                    color: isActive ? '#fff' : 'var(--lf-mid)',
                    transition: 'background .2s, color .2s, border-color .2s',
                  }}
                >
                  {category.category}
                </button>
              )
            })}
          </div>
        </Reveal>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {FAQ_CATEGORIES[activeCategory].items.map((item, index) => {
            const isOpen = openFaq === index
            return (
              <Reveal
                key={item.q}
                delay={index * 60}
                style={{ background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', borderRadius: 14, overflow: 'hidden' }}
              >
                <button
                  type="button"
                  aria-expanded={isOpen}
                  onClick={() => setOpenFaq(isOpen ? null : index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '20px 24px',
                    fontFamily: 'var(--lf-sans)',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--lf-navy)' }}>{item.q}</span>
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--lf-gold)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                    style={{
                      flexShrink: 0,
                      marginLeft: 16,
                      transition: 'transform .2s',
                      transform: isOpen ? 'rotate(180deg)' : 'none',
                    }}
                  >
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>
                {isOpen && (
                  <div style={{ padding: '0 24px 22px' }}>
                    {item.a.split('\n\n').map((paragraph, paragraphIndex) => (
                      <p
                        key={paragraphIndex}
                        style={{
                          fontSize: 15,
                          lineHeight: 2.05,
                          color: 'var(--lf-mid)',
                          marginTop: paragraphIndex > 0 ? 14 : 0,
                        }}
                      >
                        {paragraph}
                      </p>
                    ))}
                  </div>
                )}
              </Reveal>
            )
          })}
        </div>

        {showHomeLink && (
          <div style={{ textAlign: 'center', marginTop: 56 }}>
            <Link to="/" className="btn-line">홈으로</Link>
          </div>
        )}
      </div>
    </section>
  )
}
