'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

const menuKo = [
  { href: '/', label: '홈' },
  { href: '/service', label: '서비스 소개' },
  { href: '/team', label: '구성원' },
  { href: '/news', label: '소식/자료' },
  { href: '/contact', label: '상담 신청' },
]

const menuEn = [
  { href: '/', label: 'Home' },
  { href: '/service', label: 'Services' },
  { href: '/team', label: 'Team' },
  { href: '/news', label: 'News' },
  { href: '/contact', label: 'Contact' },
]

export default function Nav() {
  const pathname = usePathname()
  const [lang, setLang] = useState<'ko' | 'en'>('ko')
  const menu = lang === 'ko' ? menuKo : menuEn

  return (
    <div className="nav">
      <Link className="logo" href="/">
        PATENT<em>AI</em>
        <span>{lang === 'ko' ? '지식재산 상담 시스템' : 'IP Consultation System'}</span>
      </Link>

      <div className="menu">
        {menu.map(m => (
          <Link key={m.label} href={m.href} style={{ color: pathname === m.href ? '#C9A84C' : undefined }}>
            {m.label}
          </Link>
        ))}
      </div>

      <div className="nav-actions">
        <button
          onClick={() => setLang(l => l === 'ko' ? 'en' : 'ko')}
          style={{
            height: 34, padding: '0 .95rem',
            border: '1px solid rgba(201,168,76,.3)',
            background: 'none', color: '#C9A84C',
            fontSize: '.72rem', cursor: 'pointer',
            letterSpacing: '.1em', fontWeight: 600,
          }}
        >
          {lang === 'ko' ? 'EN' : 'KR'}
        </button>
        <Link className="login-btn" href="/login/client">
          {lang === 'ko' ? '고객 로그인' : 'Client Login'}
        </Link>
        <Link className="login-btn" href="/login/staff">
          {lang === 'ko' ? '직원 로그인' : 'Staff Login'}
        </Link>
      </div>
    </div>
  )
}
