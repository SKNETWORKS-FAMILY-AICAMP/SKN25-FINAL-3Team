'use client'
import { useEffect, useState } from 'react'

export default function ScrollProgress() {
  const [pct, setPct] = useState(0)

  useEffect(() => {
    const onScroll = () => {
      const total = document.documentElement.scrollHeight - window.innerHeight
      setPct(total > 0 ? (window.scrollY / total) * 100 : 0)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div
      style={{
        position: 'fixed', top: 0, left: 0, zIndex: 9999,
        width: `${pct}%`, height: '2px',
        background: 'linear-gradient(90deg, #8B6914, #C9A84C, #E8C97A)',
        transition: 'width 0.08s linear',
        pointerEvents: 'none',
        boxShadow: '0 0 8px rgba(201,168,76,.5)',
      }}
    />
  )
}
