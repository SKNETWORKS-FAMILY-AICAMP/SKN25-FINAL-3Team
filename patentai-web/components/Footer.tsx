'use client'

import Link from 'next/link'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function Footer() {
  const { lang } = useLang()
  const f = t.footer
  const n = t.nav

  return (
    <footer style={{ background: '#0A0A16', borderTop: '1px solid rgba(201,168,76,0.18)', padding: '3.5rem 5rem 2rem', color: '#7777A0', fontFamily: "'Noto Sans KR', sans-serif" }}>
      <style>{`
        .footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 3rem; margin-bottom: 2.5rem; }
        .footer-logo { font-family: 'Noto Serif KR', serif; color: #F0EDE6; letter-spacing: .2em; font-size: 1.1rem; margin-bottom: 1rem; }
        .footer-logo em { color: #C9A84C; font-style: normal; }
        .footer-desc { font-size: 0.82rem; line-height: 1.9; color: #7777A0; margin-bottom: 1.2rem; white-space: pre-line; }
        .footer-contact { font-size: 0.82rem; line-height: 2; color: #9999B8; }
        .footer-contact a { color: #C9A84C; text-decoration: none; }
        .footer-col-title { color: #C9A84C; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.2em; margin-bottom: 1rem; text-transform: uppercase; }
        .footer-links { display: flex; flex-direction: column; gap: 0.55rem; }
        .footer-links a { color: #9999B8; font-size: 0.82rem; text-decoration: none; transition: color 0.15s; }
        .footer-links a:hover { color: #C9A84C; }
        .footer-bottom { border-top: 1px solid rgba(201,168,76,0.12); padding-top: 1.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.76rem; flex-wrap: wrap; gap: 0.5rem; }
        .footer-badges { display: flex; gap: 1rem; }
        .footer-badge { border: 1px solid rgba(201,168,76,0.3); color: #C9A84C; font-size: 0.7rem; padding: 3px 10px; letter-spacing: 0.08em; }
        .footer-hours { white-space: pre-line; font-size: 0.82rem; color: #7777A0; line-height: 1.8; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(201,168,76,0.2); }
        @media (max-width: 900px) { .footer-grid { grid-template-columns: 1fr 1fr; gap: 2rem; } footer { padding: 2.5rem 1.5rem 1.5rem !important; } .footer-bottom { flex-direction: column; align-items: flex-start; } }
      `}</style>

      <div className="footer-grid">
        <div>
          <div className="footer-logo">PATENT<em>AI</em></div>
          <div className="footer-desc">{tr(f.desc, lang)}</div>
          <div className="footer-contact">
            <div style={{ whiteSpace: 'pre-line' }}>{tr(f.address, lang)}</div>
            <div>T. <a href="tel:02-0000-0000">02-0000-0000</a></div>
            <div>E. <a href="mailto:contact@patentai.kr">contact@patentai.kr</a></div>
          </div>
          <div className="footer-hours">
            {tr(f.hours, lang)}<br />
            <span style={{ color: '#555577', fontSize: '0.78rem' }}>{tr(f.emergency, lang)}</span>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Services</div>
          <div className="footer-links">
            <Link href="/service">{tr(n.service, lang)}</Link>
            <Link href="/service">Prior Art</Link>
            <Link href="/service">Specification</Link>
            <Link href="/service">Drawing</Link>
            <Link href="/service">Review</Link>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Company</div>
          <div className="footer-links">
            <Link href="/service">{tr(n.service, lang)}</Link>
            <Link href="/team">{tr(n.team, lang)}</Link>
            <Link href="/news">{tr(n.news, lang)}</Link>
            <Link href="/contact">{tr(n.contact, lang)}</Link>
            <Link href="/faq">{tr(n.faq, lang)}</Link>
          </div>
        </div>

        <div>
          <div className="footer-col-title">Client</div>
          <div className="footer-links">
            <Link href="/login/client">{tr(n.clientLogin, lang)}</Link>
            <Link href="/login/staff">{tr(n.staffLogin, lang)}</Link>
            <Link href="/contact">{tr(n.contact, lang)}</Link>
            <a href="https://www.kipo.go.kr" target="_blank" rel="noopener noreferrer">KIPO</a>
            <a href="https://www.kipris.or.kr" target="_blank" rel="noopener noreferrer">KIPRIS</a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.4rem' }}>
          <div>{tr(f.copyright, lang)}</div>
          <div style={{ display: 'flex', gap: '1.2rem' }}>
            <Link href="/privacy" style={{ color: '#44445A', fontSize: '.72rem', transition: 'color .15s' }}
              onMouseEnter={e => (e.currentTarget.style.color='#C9A84C')}
              onMouseLeave={e => (e.currentTarget.style.color='#44445A')}>
              {lang === 'en' ? 'Privacy Policy' : lang === 'ja' ? 'プライバシーポリシー' : lang === 'zh' ? '隐私政策' : '개인정보처리방침'}
            </Link>
            <Link href="/terms" style={{ color: '#44445A', fontSize: '.72rem', transition: 'color .15s' }}
              onMouseEnter={e => (e.currentTarget.style.color='#C9A84C')}
              onMouseLeave={e => (e.currentTarget.style.color='#44445A')}>
              {lang === 'en' ? 'Terms of Service' : lang === 'ja' ? '利用規約' : lang === 'zh' ? '服务条款' : '이용약관'}
            </Link>
          </div>
        </div>
        <div className="footer-badges">
          <span className="footer-badge">AI PATENT</span>
          <span className="footer-badge">SKN25</span>
        </div>
      </div>
    </footer>
  )
}
