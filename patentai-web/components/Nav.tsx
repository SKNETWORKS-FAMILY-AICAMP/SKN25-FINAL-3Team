'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { useLang } from '@/contexts/LangContext'
import { LANGS, t, tr } from '@/lib/i18n'

export default function Nav() {
  const pathname = usePathname()
  const { lang, setLang } = useLang()
  const [open, setOpen] = useState(false)

  const menu = [
    { href: '/',        label: tr(t.nav.home, lang) },
    { href: '/service', label: tr(t.nav.service, lang) },
    { href: '/team',    label: tr(t.nav.team, lang) },
    { href: '/news',    label: tr(t.nav.news, lang) },
    { href: '/contact', label: tr(t.nav.contact, lang) },
    { href: '/faq',     label: tr(t.nav.faq, lang) },
  ]

  return (
    <>
      <style>{`
        .lang-dropdown {
          position: relative;
          display: inline-block;
        }
        .lang-btn {
          height: 34px;
          padding: 0 .85rem;
          border: 1px solid rgba(201,168,76,.3);
          background: none;
          color: #C9A84C;
          font-size: .8rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: .35rem;
          transition: background 0.15s;
          white-space: nowrap;
        }
        .lang-btn:hover { background: rgba(201,168,76,.1); }
        .lang-menu {
          position: absolute;
          top: calc(100% + 6px);
          right: 0;
          background: #111128;
          border: 1px solid rgba(201,168,76,.25);
          min-width: 140px;
          box-shadow: 0 12px 32px rgba(0,0,0,.4);
          z-index: 999;
          animation: fadeDown 0.15s ease;
        }
        @keyframes fadeDown {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .lang-option {
          display: flex;
          align-items: center;
          gap: .6rem;
          padding: .65rem 1rem;
          color: #C8C8D8;
          font-size: .82rem;
          cursor: pointer;
          transition: background 0.12s, color 0.12s;
          border: none;
          background: none;
          width: 100%;
          text-align: left;
        }
        .lang-option:hover { background: rgba(201,168,76,.12); color: #C9A84C; }
        .lang-option.active { color: #C9A84C; font-weight: 700; }
        .lang-divider { height: 1px; background: rgba(201,168,76,.12); margin: 2px 0; }
      `}</style>

      <div className="nav">
        <Link className="logo" href="/">
          PATENT<em>AI</em>
          <span>{tr(t.nav.subtitle, lang)}</span>
        </Link>

        <div className="menu">
          {menu.map(m => (
            <Link key={m.href} href={m.href} style={{ color: pathname === m.href ? '#C9A84C' : undefined }}>
              {m.label}
            </Link>
          ))}
        </div>

        <div className="nav-actions">
          {/* 지구본 언어 드롭다운 */}
          <div className="lang-dropdown">
            <button className="lang-btn" onClick={() => setOpen(o => !o)}>
              🌐 {LANGS.find(l => l.code === lang)?.flag} {lang.toUpperCase()}
              <span style={{ fontSize: '0.6rem', opacity: 0.7 }}>▼</span>
            </button>
            {open && (
              <div className="lang-menu">
                {LANGS.map((l, i) => (
                  <div key={l.code}>
                    {i > 0 && <div className="lang-divider" />}
                    <button
                      className={`lang-option ${lang === l.code ? 'active' : ''}`}
                      onClick={() => { setLang(l.code); setOpen(false) }}
                    >
                      <span>{l.flag}</span>
                      <span>{l.label}</span>
                      {lang === l.code && <span style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>✓</span>}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Link className="login-btn" href="/login/client">{tr(t.nav.clientLogin, lang)}</Link>
          <Link className="login-btn" href="/login/staff">{tr(t.nav.staffLogin, lang)}</Link>
        </div>
      </div>
    </>
  )
}
