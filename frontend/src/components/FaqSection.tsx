import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FAQ_CATEGORIES } from '../data/faqs'
import Reveal from './Reveal'

interface Props {
  id?: string
  showHeading?: boolean
  showHomeLink?: boolean
  /** Sticky category table-of-contents alongside the full FAQ list (used on the dedicated /faq page). */
  sidebar?: boolean
}

function slugify(text: string, index: number) {
  return `faq-cat-${index}-${text.replace(/\s+/g, '')}`
}

function FaqAccordionItem({ q, a, delay }: { q: string; a: string; delay: number }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <Reveal
      delay={delay}
      style={{ background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', borderRadius: 14, overflow: 'hidden' }}
    >
      <button
        type="button"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(v => !v)}
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
        <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--lf-navy)' }}>{q}</span>
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
          {a.split('\n\n').map((paragraph, paragraphIndex) => (
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
}

export default function FaqSection({ id, showHeading = false, showHomeLink = false, sidebar = false }: Props) {
  const [activeCategory, setActiveCategory] = useState(0)
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([])

  // Scroll-spy: highlight the sidebar entry for whichever category is in view.
  useEffect(() => {
    if (!sidebar) return
    const observer = new IntersectionObserver(
      entries => {
        const visible = entries.filter(e => e.isIntersecting)
        if (visible.length === 0) return
        const topMost = visible.reduce((a, b) => (a.boundingClientRect.top < b.boundingClientRect.top ? a : b))
        const index = sectionRefs.current.findIndex(el => el === topMost.target)
        if (index !== -1) setActiveCategory(index)
      },
      { rootMargin: '-120px 0px -55% 0px', threshold: 0 },
    )
    sectionRefs.current.forEach(el => el && observer.observe(el))
    return () => observer.disconnect()
  }, [sidebar])

  if (!sidebar) {
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
                    onClick={() => setActiveCategory(index)}
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
            {FAQ_CATEGORIES[activeCategory].items.map((item, index) => (
              <FaqAccordionItem key={item.q} q={item.q} a={item.a} delay={index * 60} />
            ))}
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

  return (
    <section id={id} style={{ padding: '70px 0 150px', background: 'var(--lf-bg)', scrollMarginTop: 90 }}>
      <div className="container faq-sidebar-layout" style={{ maxWidth: 1080, display: 'flex', gap: 56, alignItems: 'flex-start' }}>
        {/* Sidebar table of contents */}
        <nav
          aria-label="FAQ 카테고리 목차"
          className="faq-sidebar-toc"
          style={{
            position: 'sticky',
            top: 110,
            flex: '0 0 200px',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
          }}
        >
          <span className="label" style={{ marginBottom: 10 }}>목차</span>
          {FAQ_CATEGORIES.map((category, index) => {
            const isActive = activeCategory === index
            return (
              <a
                key={category.category}
                href={`#${slugify(category.category, index)}`}
                style={{
                  fontSize: 14,
                  fontWeight: isActive ? 700 : 500,
                  padding: '9px 14px',
                  borderRadius: 10,
                  color: isActive ? 'var(--lf-navy)' : 'var(--lf-mid)',
                  background: isActive ? 'var(--lf-bg2)' : 'transparent',
                  borderLeft: isActive ? '2px solid var(--lf-gold)' : '2px solid transparent',
                  transition: 'background .2s, color .2s, border-color .2s',
                }}
              >
                {category.category}
              </a>
            )
          })}
        </nav>

        {/* All categories, stacked */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 64 }}>
          {FAQ_CATEGORIES.map((category, catIndex) => (
            <div
              key={category.category}
              id={slugify(category.category, catIndex)}
              ref={el => { sectionRefs.current[catIndex] = el }}
              style={{ scrollMarginTop: 110 }}
            >
              <h3 style={{ fontSize: 19, fontWeight: 800, color: 'var(--lf-navy)', marginBottom: 18 }}>
                {category.category}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {category.items.map((item, index) => (
                  <FaqAccordionItem key={item.q} q={item.q} a={item.a} delay={index * 50} />
                ))}
              </div>
            </div>
          ))}

          {showHomeLink && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Link to="/" className="btn-line">홈으로</Link>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
