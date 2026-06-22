'use client'
import { useEffect, useRef, CSSProperties } from 'react'

interface Props {
  children: React.ReactNode
  delay?: number          // ms
  direction?: 'up' | 'left' | 'right' | 'none'
  className?: string
  style?: CSSProperties
  threshold?: number
}

export default function ScrollReveal({
  children,
  delay = 0,
  direction = 'up',
  className = '',
  style = {},
  threshold = 0.12,
}: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const translate =
      direction === 'up'    ? 'translateY(28px)' :
      direction === 'left'  ? 'translateX(-28px)' :
      direction === 'right' ? 'translateX(28px)' :
      'none'

    el.style.opacity = '0'
    el.style.transform = translate
    el.style.transition = `opacity 0.65s cubic-bezier(.22,1,.36,1) ${delay}ms, transform 0.65s cubic-bezier(.22,1,.36,1) ${delay}ms`

    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.opacity = '1'
          el.style.transform = 'none'
          obs.unobserve(el)
        }
      },
      { threshold }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [delay, direction, threshold])

  return (
    <div ref={ref} className={className} style={style}>
      {children}
    </div>
  )
}
