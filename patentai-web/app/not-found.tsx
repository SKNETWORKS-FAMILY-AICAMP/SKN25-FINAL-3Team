'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export default function NotFound() {
  return (
    <div className="site">
      <Nav />
      <div style={{ minHeight: '70vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '6rem 2rem', textAlign: 'center', background: '#F7F6F3' }}>
        <style>{`
          .nf-code {
            font-family: 'Noto Serif KR', serif;
            font-size: 7rem;
            font-weight: 200;
            color: #E0DDD8;
            letter-spacing: .1em;
            line-height: 1;
            margin-bottom: 1.5rem;
          }
          .nf-line { width: 40px; height: 1px; background: #C9A84C; margin: 0 auto 2rem; }
          .nf-title { font-family: 'Noto Serif KR', serif; font-size: 1.6rem; font-weight: 300; color: #0A0A16; margin-bottom: .8rem; letter-spacing: .02em; }
          .nf-desc { font-size: .9rem; color: #777; margin-bottom: 2.5rem; line-height: 1.9; }
          .nf-actions { display: flex; gap: .8rem; justify-content: center; flex-wrap: wrap; }
          .nf-btn { padding: .8rem 2rem; font-size: .8rem; font-weight: 700; letter-spacing: .08em; cursor: pointer; text-decoration: none; border: 1px solid; display: inline-block; font-family: inherit; transition: .15s; }
          .nf-btn-primary { background: #111128; border-color: #111128; color: #C9A84C; }
          .nf-btn-primary:hover { background: #C9A84C; color: #111128; border-color: #C9A84C; }
          .nf-btn-outline { background: white; border-color: #E8E4DC; color: #444; }
          .nf-btn-outline:hover { border-color: #C9A84C; color: #C9A84C; }
        `}</style>
        <div className="nf-code">404</div>
        <div className="nf-line" />
        <div className="nf-title">페이지를 찾을 수 없습니다</div>
        <div className="nf-desc">
          요청하신 페이지가 존재하지 않거나 이동되었습니다.<br />
          아래 링크를 통해 원하시는 정보를 찾아보세요.
        </div>
        <div className="nf-actions">
          <Link href="/" className="nf-btn nf-btn-primary">홈으로 →</Link>
          <Link href="/service" className="nf-btn nf-btn-outline">서비스 보기</Link>
          <Link href="/contact" className="nf-btn nf-btn-outline">상담 신청</Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
