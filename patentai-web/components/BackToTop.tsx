'use client'
import { useEffect, useState } from 'react'

export default function BackToTop() {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 500)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <button
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      style={{
        position: 'fixed', bottom: '6rem', right: '1.8rem', zIndex: 999,
        width: '40px', height: '40px',
        background: '#111128', border: '1px solid rgba(201,168,76,.4)',
        color: '#C9A84C', cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '1rem',
        opacity: show ? 1 : 0,
        transform: show ? 'translateY(0)' : 'translateY(12px)',
        transition: 'opacity 0.25s, transform 0.25s',
        pointerEvents: show ? 'auto' : 'none',
      }}
      aria-label="맨 위로"
    >
      ↑
    </button>
  )
}
