'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useRef, useEffect } from 'react'
import { useLang } from '@/contexts/LangContext'
import { LANGS, t, tr } from '@/lib/i18n'

const menuConfig = [
  {
    href: '/',
    key: 'home',
    items: null,
  },
  {
    href: '/service',
    key: 'service',
    items: [
      { href: '/service/consultation',  num: '01', label: '특허 상담 에이전트', sub: 'Consultation Agent' },
      { href: '/service/prior-art',     num: '02', label: '선행기술 조사',       sub: 'Prior Art Search' },
      { href: '/service/specification', num: '03', label: '명세서 작성',         sub: 'Specification' },
      { href: '/service/drawing',       num: '04', label: '도면 자동 생성',      sub: 'Drawing Agent' },
      { href: '/service/review',        num: '05', label: '심사 대응',           sub: 'Patent Review' },
    ],
  },
  {
    href: '/team',
    key: 'team',
    items: [
      { href: '/team/gayeongkwon',  num: '01', label: '권가영', sub: 'Prior Art Agent' },
      { href: '/team/seohyunkim',   num: '02', label: '김서현', sub: 'Frontend / PatentAI UI' },
      { href: '/team/hongikkim',    num: '03', label: '김홍익', sub: 'Consultation Agent' },
      { href: '/team/beomsoopark',  num: '04', label: '박범수', sub: 'Specification / Claims' },
      { href: '/team/eunseokjo',    num: '05', label: '조은석', sub: 'Drawing Agent' },
      { href: '/team/hyeonwoochoi', num: '06', label: '최현우', sub: 'Review / Integration' },
    ],
  },
  {
    href: '/news',
    key: 'news',
    items: [
      { href: '/news/ai-patent',      num: '01', label: 'AI 특허 동향',   sub: 'AI Patent Trends' },
      { href: '/news/prior-art',      num: '02', label: '선행기술 자료',   sub: 'Prior Art Resources' },
      { href: '/news/policy',         num: '03', label: '특허청 정책',     sub: 'KIPO Policy' },
      { href: '/news/classification', num: '04', label: 'IPC / CPC 분류', sub: 'Classification' },
    ],
  },
  {
    href: '/contact',
    key: 'contact',
    items: [
      { href: '/contact', num: '01', label: '상담 신청',  sub: 'Request Consultation' },
      { href: '/contact', num: '02', label: '이메일 문의', sub: 'contact@patentai.kr' },
      { href: '/contact', num: '03', label: '전화 문의',  sub: '02-0000-0000' },
    ],
  },
  {
    href: '/faq',
    key: 'faq',
    items: [
      { href: '/faq?cat=filing',   num: '01', label: '특허 출원',        sub: 'Patent Filing' },
      { href: '/faq?cat=service',  num: '02', label: 'PatentAI 서비스',  sub: 'Our Service' },
      { href: '/faq?cat=cost',     num: '03', label: '비용 · 기간',      sub: 'Cost & Timeline' },
      { href: '/faq?cat=usage',    num: '04', label: '이용 방법',        sub: 'How to Use' },
    ],
  },
]

export default function Nav() {
  const pathname = usePathname()
  const { lang, setLang } = useLang()
  const [activeMenu, setActiveMenu] = useState<string | null>(null)
  const [langOpen, setLangOpen]     = useState(false)
  const langRef  = useRef<HTMLDivElement>(null)
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (langRef.current && !langRef.current.contains(e.target as Node)) setLangOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  function onEnter(key: string) {
    if (leaveTimer.current) clearTimeout(leaveTimer.current)
    setActiveMenu(key)
  }

  function onLeave() {
    leaveTimer.current = setTimeout(() => setActiveMenu(null), 120)
  }

  const labels: Record<string, string> = {
    home: tr(t.nav.home, lang),
    service: tr(t.nav.service, lang),
    team: tr(t.nav.team, lang),
    news: tr(t.nav.news, lang),
    contact: tr(t.nav.contact, lang),
    faq: tr(t.nav.faq, lang),
  }

  return (
    <>
      <style>{`
        .nav-item-wrap {
          position: relative;
          display: inline-flex; align-items: center;
        }
        .nav-link {
          color: #C8C8D8; font-size: .78rem; font-weight: 600;
          text-decoration: none; transition: color 0.15s;
          padding: 4px 0;
          border-bottom: 2px solid transparent;
          transition: color 0.15s, border-color 0.15s;
        }
        .nav-link:hover, .nav-link.active { color: #C9A84C; }
        .nav-link.active { border-bottom-color: #C9A84C; }

        .nav-dropdown {
          position: absolute;
          top: calc(100% + 18px);
          left: 50%;
          transform: translateX(-50%);
          background: #0D0D20;
          border: 1px solid rgba(201,168,76,.2);
          border-top: 2px solid #C9A84C;
          min-width: 260px;
          box-shadow: 0 20px 48px rgba(0,0,0,.55);
          z-index: 9000;
          animation: dropFade 0.15s ease;
        }
        .nav-dropdown::before {
          content: '';
          position: absolute;
          top: -7px; left: 50%;
          width: 12px; height: 12px;
          background: #0D0D20;
          border-left: 1px solid rgba(201,168,76,.2);
          border-top: 1px solid rgba(201,168,76,.2);
          transform: translateX(-50%) rotate(45deg);
        }
        @keyframes dropFade {
          from { opacity: 0; transform: translateX(-50%) translateY(-6px); }
          to   { opacity: 1; transform: translateX(-50%) translateY(0); }
        }

        .nav-drop-item {
          display: flex; align-items: center; gap: 1rem;
          padding: .85rem 1.3rem; text-decoration: none;
          border-bottom: 1px solid rgba(255,255,255,.04);
          transition: background 0.1s;
        }
        .nav-drop-item:last-child { border-bottom: none; }
        .nav-drop-item:hover { background: rgba(201,168,76,.07); }
        .nav-drop-item:hover .dnum { color: #C9A84C; }
        .nav-drop-item:hover .dlabel { color: #F0EDE6; }

        .dnum {
          font-family: 'Noto Serif KR', serif;
          font-size: .7rem; color: #444466;
          font-weight: 300; flex-shrink: 0; width: 18px;
          transition: color 0.1s;
        }
        .dtext { display: flex; flex-direction: column; gap: 1px; }
        .dlabel {
          color: #C8C8D8; font-size: .82rem; font-weight: 600;
          transition: color 0.1s;
        }
        .dsub { color: #444466; font-size: .68rem; letter-spacing: .06em; }

        .nav-drop-footer {
          display: flex; align-items: center; justify-content: space-between;
          padding: .65rem 1.3rem; text-decoration: none;
          background: rgba(201,168,76,.05);
          border-top: 1px solid rgba(201,168,76,.12);
          transition: background 0.1s;
        }
        .nav-drop-footer:hover { background: rgba(201,168,76,.1); }
        .nav-drop-footer span { color: #C9A84C; font-size: .72rem; font-weight: 700; letter-spacing: .1em; }

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
          z-index: 9000; animation: dropFade2 0.15s ease;
        }
        @keyframes dropFade2 {
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

        <div className="menu" style={{ gap: '1.8rem' }}>
          {menuConfig.map(m => {
            const isActive = pathname === m.href || (m.href !== '/' && pathname.startsWith(m.href))
            const label = labels[m.key]

            if (!m.items) {
              return (
                <Link key={m.key} href={m.href} className={`nav-link ${isActive ? 'active' : ''}`}>
                  {label}
                </Link>
              )
            }

            return (
              <div
                key={m.key}
                className="nav-item-wrap"
                onMouseEnter={() => onEnter(m.key)}
                onMouseLeave={onLeave}
              >
                <Link href={m.href} className={`nav-link ${isActive ? 'active' : ''}`}>
                  {label}
                </Link>

                {activeMenu === m.key && (
                  <div className="nav-dropdown" onMouseEnter={() => onEnter(m.key)} onMouseLeave={onLeave}>
                    {m.items.map(item => (
                      <Link key={item.num} className="nav-drop-item" href={item.href}>
                        <span className="dnum">{item.num}</span>
                        <span className="dtext">
                          <span className="dlabel">{item.label}</span>
                          <span className="dsub">{item.sub}</span>
                        </span>
                      </Link>
                    ))}
                    <Link className="nav-drop-footer" href={m.href}>
                      <span>전체 보기</span>
                      <span style={{ color: '#C9A84C' }}>→</span>
                    </Link>
                  </div>
                )}
              </div>
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
