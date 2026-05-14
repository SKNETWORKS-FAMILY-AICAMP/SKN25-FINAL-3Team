'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useRef, useEffect } from 'react'
import { useLang } from '@/contexts/LangContext'
import { LANGS, t, tr } from '@/lib/i18n'

// ── 메뉴 설정 ─────────────────────────────────────────────
const menuConfig = [
  {
    href: '/service',
    key: 'agent',
    label: '에이전트',
    items: [
      { href: '/service/consultation',  num: '01', label: '특허 상담 에이전트', sub: 'Consultation' },
      { href: '/service/prior-art',     num: '02', label: '선행기술 조사',       sub: 'Prior Art Search' },
      { href: '/service/specification', num: '03', label: '명세서 작성',         sub: 'Specification' },
      { href: '/service/drawing',       num: '04', label: '도면 자동 생성',      sub: 'Drawing Agent' },
      { href: '/service/review',        num: '05', label: '심사 대응',           sub: 'Patent Review' },
    ],
    footer: { href: '/gallery', label: '도면 갤러리 보기' },
  },
  {
    href: '/team',
    key: 'team',
    label: '구성원',
    items: [
      { href: '/team/gayeongkwon',  num: '01', label: '권가영', sub: 'Prior Art Agent' },
      { href: '/team/seohyunkim',   num: '02', label: '김서현', sub: 'Frontend / UI' },
      { href: '/team/hongikkim',    num: '03', label: '김홍익', sub: 'Consultation' },
      { href: '/team/beomsoopark',  num: '04', label: '박범수', sub: 'Specification' },
      { href: '/team/eunseokjo',    num: '05', label: '조은석', sub: 'Drawing Agent' },
      { href: '/team/hyeonwoochoi', num: '06', label: '최현우', sub: 'Integration' },
    ],
    footer: { href: '/team', label: '구성원 전체 보기' },
  },
  {
    href: '/news',
    key: 'news',
    label: '소식/자료',
    items: [
      { href: '/news/ai-patent',      num: '01', label: 'AI 특허 동향',   sub: 'AI Patent Trends' },
      { href: '/news/prior-art',      num: '02', label: '선행기술 자료',   sub: 'Prior Art' },
      { href: '/news/policy',         num: '03', label: '특허청 정책',     sub: 'KIPO Policy' },
      { href: '/news/classification', num: '04', label: 'IPC / CPC 분류', sub: 'Classification' },
    ],
    footer: { href: '/news', label: '전체 소식 보기' },
  },
  { href: '/contact', key: 'contact', label: '상담 신청', items: null },
  { href: '/faq',     key: 'faq',     label: 'FAQ',       items: null },
  { href: '/about',   key: 'about',   label: 'PatentAI 소개', items: null },
  { href: '/careers', key: 'careers', label: '인재채용',   items: null },
]

// ── 로고 SVG ─────────────────────────────────────────────
function Logo() {
  return (
    <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none', marginRight: '3rem', flexShrink: 0 }}>
      {/* 아이콘 마크 */}
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
        <rect width="36" height="36" fill="#0A0A16"/>
        <rect x="1" y="1" width="34" height="34" stroke="#C9A84C" strokeWidth="1"/>
        {/* P 모양 특허 심볼 */}
        <path d="M10 10 L10 26" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round"/>
        <path d="M10 10 L17 10 Q22 10 22 15 Q22 20 17 20 L10 20" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        {/* AI 점 */}
        <circle cx="26" cy="22" r="1.5" fill="#C9A84C"/>
        <circle cx="26" cy="26" r="1.5" fill="#C9A84C" opacity="0.5"/>
      </svg>
      {/* 워드마크 */}
      <div>
        <div style={{
          fontFamily: "'Noto Serif KR', serif",
          color: '#F0EDE6',
          letterSpacing: '.2em',
          fontSize: '0.95rem',
          fontWeight: 300,
          lineHeight: 1.2,
        }}>
          PATENT<span style={{ color: '#C9A84C' }}>AI</span>
        </div>
        <div style={{ color: '#444466', fontSize: '0.58rem', letterSpacing: '.12em', marginTop: '2px' }}>
          IP CONSULTATION
        </div>
      </div>
    </Link>
  )
}

// ── 검색 아이콘 ───────────────────────────────────────────
function SearchIcon() {
  const [open, setOpen] = useState(false)
  const [val, setVal]   = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { if (open) inputRef.current?.focus() }, [open])

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      {open && (
        <input
          ref={inputRef}
          value={val}
          onChange={e => setVal(e.target.value)}
          onKeyDown={e => e.key === 'Escape' && setOpen(false)}
          placeholder="검색어를 입력하세요"
          style={{
            position: 'absolute', right: '28px',
            width: 220, height: 32,
            background: 'rgba(255,255,255,.06)',
            border: 'none', borderBottom: '1px solid rgba(201,168,76,.5)',
            color: '#F0EDE6', fontSize: '.78rem', padding: '0 .8rem',
            outline: 'none', fontFamily: 'inherit',
            animation: 'fadeIn .15s ease',
          }}
        />
      )}
      <button
        onClick={() => setOpen(o => !o)}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center' }}
      >
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#9999B8" strokeWidth="1.8" strokeLinecap="round">
          <circle cx="11" cy="11" r="7"/>
          <line x1="16.5" y1="16.5" x2="21" y2="21"/>
        </svg>
      </button>
    </div>
  )
}

export default function Nav() {
  const pathname = usePathname()
  const { lang, setLang } = useLang()
  const [activeMenu, setActiveMenu]   = useState<string | null>(null)
  const [langOpen, setLangOpen]       = useState(false)
  const [loginOpen, setLoginOpen]     = useState(false)
  const langRef  = useRef<HTMLDivElement>(null)
  const loginRef = useRef<HTMLDivElement>(null)
  const leaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (langRef.current  && !langRef.current.contains(e.target as Node))  setLangOpen(false)
      if (loginRef.current && !loginRef.current.contains(e.target as Node)) setLoginOpen(false)
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

  return (
    <>
      <style>{`
        /* ── 드롭다운 공통 ── */
        .nav-item-wrap { position: relative; display: inline-flex; align-items: center; }
        .nav-link {
          color: #9999B8; font-size: .75rem; font-weight: 500;
          text-decoration: none; padding: 4px 0;
          border-bottom: 1px solid transparent;
          transition: color .15s, border-color .15s;
          letter-spacing: .02em;
        }
        .nav-link:hover, .nav-link.active { color: #F0EDE6; }
        .nav-link.active { border-bottom-color: #C9A84C; }

        .nav-dropdown {
          position: absolute; top: calc(100% + 20px); left: 50%;
          transform: translateX(-50%);
          background: #08081A;
          border: 1px solid rgba(201,168,76,.15);
          border-top: 1px solid #C9A84C;
          min-width: 260px;
          box-shadow: 0 24px 56px rgba(0,0,0,.6);
          z-index: 9000;
          animation: dropFade .15s ease;
        }
        .nav-dropdown::before {
          content: ''; position: absolute;
          top: -6px; left: 50%;
          width: 10px; height: 10px;
          background: #08081A;
          border-left: 1px solid rgba(201,168,76,.15);
          border-top: 1px solid #C9A84C;
          transform: translateX(-50%) rotate(45deg);
        }
        @keyframes dropFade {
          from { opacity: 0; transform: translateX(-50%) translateY(-6px); }
          to   { opacity: 1; transform: translateX(-50%) translateY(0); }
        }

        .nav-drop-item {
          display: flex; align-items: center; gap: 1rem;
          padding: .8rem 1.3rem; text-decoration: none;
          border-bottom: 1px solid rgba(255,255,255,.03);
          transition: background .1s;
        }
        .nav-drop-item:last-child { border-bottom: none; }
        .nav-drop-item:hover { background: rgba(201,168,76,.06); }
        .nav-drop-item:hover .dnum  { color: #C9A84C; }
        .nav-drop-item:hover .dlabel { color: #F0EDE6; }

        .dnum   { font-family:'Noto Serif KR',serif; font-size:.68rem; color:#333355; font-weight:300; flex-shrink:0; width:18px; transition:color .1s; }
        .dtext  { display:flex; flex-direction:column; gap:1px; }
        .dlabel { color:#C0C0D0; font-size:.8rem; font-weight:600; transition:color .1s; }
        .dsub   { color:#333355; font-size:.66rem; letter-spacing:.06em; }

        .nav-drop-footer {
          display: flex; align-items: center; justify-content: space-between;
          padding: .6rem 1.3rem; text-decoration: none;
          background: rgba(201,168,76,.04);
          border-top: 1px solid rgba(201,168,76,.1);
          transition: background .1s;
        }
        .nav-drop-footer:hover { background: rgba(201,168,76,.1); }
        .nav-drop-footer span { color: #C9A84C; font-size: .7rem; font-weight: 700; letter-spacing: .1em; }

        /* ── 로그인 드롭다운 ── */
        .login-dropdown { position: relative; display: inline-block; }
        .login-trigger {
          height: 32px; padding: 0 1rem;
          border: 1px solid rgba(201,168,76,.3);
          color: #9999B8; display: flex; align-items: center;
          font-size: .7rem; background: none; cursor: pointer;
          letter-spacing: .06em; transition: .15s; gap: .4rem;
        }
        .login-trigger:hover { color: #C9A84C; border-color: rgba(201,168,76,.7); }
        .login-menu {
          position: absolute; top: calc(100% + 6px); right: 0;
          background: #08081A;
          border: 1px solid rgba(201,168,76,.2);
          border-top: 1px solid #C9A84C;
          min-width: 160px;
          box-shadow: 0 16px 40px rgba(0,0,0,.5);
          z-index: 9000;
          animation: loginDrop .15s ease;
        }
        @keyframes loginDrop {
          from { opacity:0; transform:translateY(-4px); }
          to   { opacity:1; transform:translateY(0); }
        }
        .login-option {
          display: block; padding: .75rem 1.2rem;
          color: #C0C0D0; font-size: .78rem; font-weight: 500;
          text-decoration: none; transition: background .1s, color .1s;
          border-bottom: 1px solid rgba(255,255,255,.04);
          letter-spacing: .03em;
        }
        .login-option:last-child { border-bottom: none; }
        .login-option:hover { background: rgba(201,168,76,.08); color: #C9A84C; }
        .login-option-sub { color: #444466; font-size: .65rem; margin-top: 1px; letter-spacing: .06em; }

        /* ── 언어 드롭다운 ── */
        .lang-wrap { position: relative; display: inline-flex; align-items: center; }
        .lang-trigger {
          background: none; border: none; cursor: pointer;
          padding: 4px; display: flex; align-items: center;
          transition: opacity .15s;
        }
        .lang-trigger:hover { opacity: .7; }
        .lang-menu {
          position: absolute; top: calc(100% + 8px); right: 0;
          background: #08081A;
          border: 1px solid rgba(201,168,76,.2);
          min-width: 130px;
          box-shadow: 0 12px 32px rgba(0,0,0,.5);
          z-index: 9000;
          animation: loginDrop .15s ease;
        }
        .lang-opt {
          display: flex; align-items: center; gap: .55rem;
          padding: .6rem 1rem; color: #9999B8; font-size: .78rem;
          cursor: pointer; transition: .1s;
          border: none; background: none; width: 100%; text-align: left;
          font-family: inherit;
          border-bottom: 1px solid rgba(255,255,255,.03);
        }
        .lang-opt:last-child { border-bottom: none; }
        .lang-opt:hover { background: rgba(201,168,76,.08); color: #C9A84C; }
        .lang-opt.active { color: #C9A84C; font-weight: 700; }

        @keyframes fadeIn { from{opacity:0;}to{opacity:1;} }
      `}</style>

      <div className="nav">
        <Logo />

        {/* 메인 메뉴 */}
        <div className="menu" style={{ gap: '2rem' }}>
          {menuConfig.map(m => {
            const isActive = pathname === m.href || (m.href !== '/' && pathname.startsWith(m.href))

            if (!m.items) {
              return (
                <Link key={m.key} href={m.href} className={`nav-link ${isActive ? 'active' : ''}`}>
                  {m.label}
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
                <Link href={m.href} className={`nav-link ${isActive ? 'active' : ''}`}>{m.label}</Link>

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
                    {m.footer && (
                      <Link className="nav-drop-footer" href={m.footer.href}>
                        <span>{m.footer.label}</span>
                        <span style={{ color:'#C9A84C', fontSize:'.9rem' }}>→</span>
                      </Link>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* 우측 아이콘 영역 */}
        <div className="nav-actions" style={{ gap: '.8rem' }}>
          {/* 검색 */}
          <SearchIcon />

          {/* 언어 전환 */}
          <div className="lang-wrap" ref={langRef}>
            <button className="lang-trigger" onClick={() => setLangOpen(o => !o)}>
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#9999B8" strokeWidth="1.6" strokeLinecap="round">
                <circle cx="12" cy="12" r="9"/>
                <path d="M3 12h18M12 3c-2.5 3-4 5.5-4 9s1.5 6 4 9M12 3c2.5 3 4 5.5 4 9s-1.5 6-4 9"/>
              </svg>
            </button>
            {langOpen && (
              <div className="lang-menu">
                {LANGS.map(l => (
                  <button
                    key={l.code}
                    className={`lang-opt ${lang === l.code ? 'active' : ''}`}
                    onClick={() => { setLang(l.code); setLangOpen(false) }}
                  >
                    <span>{l.flag}</span>
                    <span>{l.label}</span>
                    {lang === l.code && <span style={{ marginLeft:'auto', color:'#C9A84C' }}>✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 로그인 드롭다운 — 아이콘만 */}
          <div className="login-dropdown" ref={loginRef}>
            <button
              className="login-trigger"
              style={{ padding:'4px 6px', border:'none', background:'none', cursor:'pointer' }}
              onMouseEnter={() => setLoginOpen(true)}
              onClick={() => setLoginOpen(o => !o)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9999B8" strokeWidth="1.6" strokeLinecap="round">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
              </svg>
            </button>
            {loginOpen && (
              <div className="login-menu" onMouseLeave={() => setLoginOpen(false)}>
                <Link className="login-option" href="/login/client" onClick={() => setLoginOpen(false)}>
                  {tr(t.nav.clientLogin, lang)}
                  <div className="login-option-sub">CLIENT ACCESS</div>
                </Link>
                <Link className="login-option" href="/login/staff" onClick={() => setLoginOpen(false)}>
                  {tr(t.nav.staffLogin, lang)}
                  <div className="login-option-sub">STAFF ACCESS</div>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
