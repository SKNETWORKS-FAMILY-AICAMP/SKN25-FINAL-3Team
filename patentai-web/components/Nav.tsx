'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useRef, useEffect } from 'react'
import { useLang } from '@/contexts/LangContext'
import { LANGS, t, tr } from '@/lib/i18n'

const serviceItems = [
  { href: '/service', label: '특허 상담 에이전트',  sub: 'Consultation Agent',  num: '01' },
  { href: '/service', label: '선행기술 조사',        sub: 'Prior Art Search',    num: '02' },
  { href: '/service', label: '명세서 작성',          sub: 'Specification',       num: '03' },
  { href: '/service', label: '도면 자동 생성',       sub: 'Drawing Agent',       num: '04' },
  { href: '/service', label: '심사 대응',            sub: 'Patent Review',       num: '05' },
]

export default function Nav() {
  const pathname   = usePathname()
  const { lang, setLang } = useLang()
  const [langOpen, setLangOpen]       = useState(false)
  const [serviceOpen, setServiceOpen] = useState(false)
  const serviceRef = useRef<HTMLDivElement>(null)
  const langRef    = useRef<HTMLDivElement>(null)

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (serviceRef.current && !serviceRef.current.contains(e.target as Node)) setServiceOpen(false)
      if (langRef.current    && !langRef.current.contains(e.target as Node))    setLangOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  const menu = [
    { href: '/',        label: tr(t.nav.home, lang),    dropdown: false },
    { href: '/service', label: tr(t.nav.service, lang), dropdown: true },
    { href: '/team',    label: tr(t.nav.team, lang),    dropdown: false },
    { href: '/news',    label: tr(t.nav.news, lang),    dropdown: false },
    { href: '/contact', label: tr(t.nav.contact, lang), dropdown: false },
    { href: '/faq',     label: tr(t.nav.faq, lang),     dropdown: false },
  ]

  return (
    <>
      <style>{`
        /* 서비스 드롭다운 */
        .svc-dropdown { position: relative; display: inline-flex; align-items: center; }
        .svc-trigger {
          display: flex; align-items: center; gap: 4px;
          color: #C8C8D8; font-size: .78rem; font-weight: 600;
          background: none; border: none; cursor: pointer;
          font-family: inherit; padding: 0; transition: color 0.15s;
        }
        .svc-trigger:hover { color: #C9A84C; }
        .svc-trigger.active { color: #C9A84C; }
        .svc-caret {
          font-size: 0.55rem; opacity: 0.7;
          transition: transform 0.2s;
          display: inline-block;
        }
        .svc-caret.open { transform: rotate(180deg); }

        .svc-menu {
          position: absolute;
          top: calc(100% + 16px);
          left: 50%;
          transform: translateX(-50%);
          background: #0D0D20;
          border: 1px solid rgba(201,168,76,.2);
          border-top: 2px solid #C9A84C;
          min-width: 280px;
          box-shadow: 0 20px 48px rgba(0,0,0,.5);
          z-index: 9000;
          animation: dropDown 0.18s ease;
        }
        .svc-menu::before {
          content: '';
          position: absolute; top: -7px; left: 50%;
          transform: translateX(-50%);
          width: 12px; height: 12px;
          background: #0D0D20;
          border-left: 1px solid rgba(201,168,76,.2);
          border-top: 1px solid rgba(201,168,76,.2);
          transform: translateX(-50%) rotate(45deg);
        }
        @keyframes dropDown {
          from { opacity: 0; transform: translateX(-50%) translateY(-8px); }
          to   { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        .svc-item {
          display: flex; align-items: center; gap: 1rem;
          padding: .9rem 1.4rem; text-decoration: none;
          transition: background 0.12s;
          border-bottom: 1px solid rgba(255,255,255,.04);
        }
        .svc-item:last-child { border-bottom: none; }
        .svc-item:hover { background: rgba(201,168,76,.08); }
        .svc-item:hover .svc-item-num { color: #C9A84C; }
        .svc-item:hover .svc-item-label { color: #F0EDE6; }
        .svc-item-num {
          font-family: 'Noto Serif KR', serif;
          font-size: .72rem; color: #555577;
          font-weight: 300; flex-shrink: 0; width: 20px;
          transition: color 0.12s;
        }
        .svc-item-text { display: flex; flex-direction: column; gap: 2px; }
        .svc-item-label {
          color: #C8C8D8; font-size: .84rem; font-weight: 600;
          transition: color 0.12s;
        }
        .svc-item-sub { color: #555577; font-size: .7rem; letter-spacing: .08em; }
        .svc-view-all {
          display: flex; align-items: center; justify-content: space-between;
          padding: .75rem 1.4rem; text-decoration: none;
          background: rgba(201,168,76,.06);
          border-top: 1px solid rgba(201,168,76,.15);
        }
        .svc-view-all span { color: #C9A84C; font-size: .76rem; font-weight: 700; letter-spacing: .1em; }
        .svc-view-all:hover { background: rgba(201,168,76,.12); }

        /* 언어 드롭다운 */
        .lang-dropdown { position: relative; display: inline-block; }
        .lang-btn {
          height: 34px; padding: 0 .85rem;
          border: 1px solid rgba(201,168,76,.3);
          background: none; color: #C9A84C; font-size: .8rem;
          cursor: pointer; display: flex; align-items: center;
          gap: .35rem; transition: background 0.15s; white-space: nowrap;
        }
        .lang-btn:hover { background: rgba(201,168,76,.1); }
        .lang-menu {
          position: absolute; top: calc(100% + 6px); right: 0;
          background: #111128; border: 1px solid rgba(201,168,76,.25);
          min-width: 140px; box-shadow: 0 12px 32px rgba(0,0,0,.4);
          z-index: 9000; animation: fadeDown 0.15s ease;
        }
        @keyframes fadeDown {
          from { opacity: 0; transform: translateY(-6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .lang-option {
          display: flex; align-items: center; gap: .6rem;
          padding: .65rem 1rem; color: #C8C8D8; font-size: .82rem;
          cursor: pointer; transition: background 0.12s, color 0.12s;
          border: none; background: none; width: 100%; text-align: left;
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
          {menu.map(m => {
            if (m.dropdown) {
              return (
                <div className="svc-dropdown" key={m.href} ref={serviceRef}>
                  <button
                    className={`svc-trigger ${pathname.startsWith('/service') ? 'active' : ''}`}
                    onClick={() => setServiceOpen(o => !o)}
                  >
                    {m.label}
                    <span className={`svc-caret ${serviceOpen ? 'open' : ''}`}>▼</span>
                  </button>

                  {serviceOpen && (
                    <div className="svc-menu">
                      {serviceItems.map(s => (
                        <Link
                          key={s.num}
                          className="svc-item"
                          href={s.href}
                          onClick={() => setServiceOpen(false)}
                        >
                          <span className="svc-item-num">{s.num}</span>
                          <span className="svc-item-text">
                            <span className="svc-item-label">{s.label}</span>
                            <span className="svc-item-sub">{s.sub}</span>
                          </span>
                        </Link>
                      ))}
                      <Link className="svc-view-all" href="/service" onClick={() => setServiceOpen(false)}>
                        <span>전체 서비스 보기</span>
                        <span style={{ color: '#C9A84C', fontSize: '0.9rem' }}>→</span>
                      </Link>
                    </div>
                  )}
                </div>
              )
            }
            return (
              <Link key={m.href} href={m.href} style={{ color: pathname === m.href ? '#C9A84C' : undefined }}>
                {m.label}
              </Link>
            )
          })}
        </div>

        <div className="nav-actions">
          <div className="lang-dropdown" ref={langRef}>
            <button className="lang-btn" onClick={() => setLangOpen(o => !o)}>
              🌐 {LANGS.find(l => l.code === lang)?.flag} {lang.toUpperCase()}
              <span style={{ fontSize: '0.6rem', opacity: 0.7 }}>▼</span>
            </button>
            {langOpen && (
              <div className="lang-menu">
                {LANGS.map((l, i) => (
                  <div key={l.code}>
                    {i > 0 && <div className="lang-divider" />}
                    <button
                      className={`lang-option ${lang === l.code ? 'active' : ''}`}
                      onClick={() => { setLang(l.code); setLangOpen(false) }}
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
