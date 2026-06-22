'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const items = [
  {
    href: '/',
    label: '홈',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A84C' : '#666688'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z"/>
        <path d="M9 21V12h6v9"/>
      </svg>
    ),
  },
  {
    href: '/service',
    label: '에이전트',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A84C' : '#666688'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        <circle cx="12" cy="16" r="1.5" fill={active ? '#C9A84C' : '#666688'} stroke="none"/>
      </svg>
    ),
  },
  {
    href: '/contact',
    label: '상담',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A84C' : '#666688'} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  },
  {
    href: '/faq',
    label: 'FAQ',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A84C' : '#666688'} strokeWidth="1.8" strokeLinecap="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M9.5 9a2.5 2.5 0 0 1 5 .5c0 2-3 2.5-3 4.5"/>
        <circle cx="12" cy="18" r=".5" fill={active ? '#C9A84C' : '#666688'}/>
      </svg>
    ),
  },
  {
    href: '/team',
    label: '구성원',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? '#C9A84C' : '#666688'} strokeWidth="1.8" strokeLinecap="round">
        <circle cx="9" cy="7" r="3"/>
        <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/>
        <circle cx="17" cy="8" r="2.5"/>
        <path d="M21 20c0-2.8-2-5-4.5-5.5"/>
      </svg>
    ),
  },
]

export default function MobileNav() {
  const pathname = usePathname()

  return (
    <nav style={{
      display: 'none',
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: '#08081A',
      borderTop: '1px solid rgba(201,168,76,.15)',
      zIndex: 999,
      paddingBottom: 'env(safe-area-inset-bottom)',
    }}
    className="mobile-nav"
    >
      <style>{`
        @media (max-width: 768px) {
          .mobile-nav { display: flex !important; }
          body { padding-bottom: 72px; }
        }
      `}</style>
      {items.map(item => {
        const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href))
        return (
          <Link
            key={item.href}
            href={item.href}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              padding: '0.7rem 0.5rem 0.5rem',
              textDecoration: 'none', gap: '4px',
            }}
          >
            {item.icon(active)}
            <span style={{
              fontSize: '0.62rem', fontWeight: active ? 700 : 400,
              color: active ? '#C9A84C' : '#444466',
              letterSpacing: '0.02em',
              fontFamily: "'Noto Sans KR', sans-serif",
            }}>
              {item.label}
            </span>
          </Link>
        )
      })}
    </nav>
  )
}
