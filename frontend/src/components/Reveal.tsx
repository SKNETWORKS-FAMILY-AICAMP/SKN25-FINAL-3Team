import { useEffect, useRef, useState, ReactNode, CSSProperties } from 'react'

interface Props {
  children: ReactNode
  delay?: number
  style?: CSSProperties
  className?: string
  /** 'fade' = 아래에서 위로 페이드인 (기본), 'scale' = Apple 스타일 확대+블러 해제 */
  variant?: 'fade' | 'scale'
}

export default function Reveal({ children, delay = 0, style, className, variant = 'fade' }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.15 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const hidden: CSSProperties =
    variant === 'scale'
      ? { opacity: 0, transform: 'scale(.92)', filter: 'blur(6px)' }
      : { opacity: 0, transform: 'translateY(28px)', filter: 'blur(0px)' }
  const shown: CSSProperties = { opacity: 1, transform: 'scale(1) translateY(0)', filter: 'blur(0px)' }

  return (
    <div
      ref={ref}
      className={className}
      style={{
        ...(visible ? shown : hidden),
        transition: `opacity .9s var(--lf-ease) ${delay}ms, transform .9s var(--lf-ease) ${delay}ms, filter .9s var(--lf-ease) ${delay}ms`,
        ...style,
      }}
    >
      {children}
    </div>
  )
}