'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Nav() {
  const pathname = usePathname()

  return (
    <div className="nav">
      <Link className="logo" href="/">
        PATENT<em>AI</em>
        <span>지식재산 상담 시스템</span>
      </Link>

      <div className="menu">
        <Link href="/" style={{ color: pathname === '/' ? '#C9A84C' : undefined }}>홈</Link>
        <Link href="/service" style={{ color: pathname === '/service' ? '#C9A84C' : undefined }}>서비스 소개</Link>
        <Link href="/team" style={{ color: pathname === '/team' ? '#C9A84C' : undefined }}>구성원</Link>
        <Link href="/news" style={{ color: pathname === '/news' ? '#C9A84C' : undefined }}>소식/자료</Link>
      </div>

      <div className="nav-actions">
        <Link className="login-btn" href="/login/client">고객 로그인</Link>
        <Link className="login-btn" href="/login/staff">직원 로그인</Link>
      </div>
    </div>
  )
}
