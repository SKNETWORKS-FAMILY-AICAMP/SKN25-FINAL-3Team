'use client'

import { useState, useEffect } from 'react'

export default function CookieBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem('cookie-consent')) setVisible(true)
  }, [])

  function accept() {
    localStorage.setItem('cookie-consent', 'accepted')
    setVisible(false)
  }

  function decline() {
    localStorage.setItem('cookie-consent', 'declined')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: '#111128', borderTop: '2px solid rgba(201,168,76,0.3)',
      padding: '1.2rem 2rem', zIndex: 99999,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      flexWrap: 'wrap', gap: '1rem',
      boxShadow: '0 -8px 32px rgba(0,0,0,0.3)',
      fontFamily: "'Noto Sans KR', sans-serif",
    }}>
      <div style={{ flex: 1, minWidth: 260 }}>
        <div style={{ color: '#F0EDE6', fontSize: '0.88rem', fontWeight: 600, marginBottom: '0.3rem' }}>
          🍪 쿠키 사용 안내
        </div>
        <div style={{ color: '#9999B8', fontSize: '0.8rem', lineHeight: 1.6 }}>
          PatentAI는 서비스 품질 향상을 위해 쿠키를 사용합니다.
          자세한 내용은 개인정보처리방침을 확인해 주세요.
        </div>
      </div>
      <div style={{ display: 'flex', gap: '0.6rem', flexShrink: 0 }}>
        <button onClick={decline} style={{
          height: 38, padding: '0 1.2rem',
          border: '1px solid rgba(201,168,76,0.3)', background: 'none',
          color: '#9999B8', fontSize: '0.82rem', cursor: 'pointer',
          transition: '0.15s',
        }}>
          거부
        </button>
        <button onClick={accept} style={{
          height: 38, padding: '0 1.5rem',
          border: '1px solid #C9A84C', background: '#C9A84C',
          color: '#111128', fontSize: '0.82rem', fontWeight: 700,
          cursor: 'pointer', transition: '0.15s',
        }}>
          동의
        </button>
      </div>
    </div>
  )
}
