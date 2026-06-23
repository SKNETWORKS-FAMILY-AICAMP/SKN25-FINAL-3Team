import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const NAV_ITEMS = [
  { label: 'AI 에이전트', hash: 'pipeline' },
  { label: '청구항 심사', path: '/claim-review' },
  { label: 'FAQ', path: '/faq' },
] as const

const FEATURE_LINKS = [
  { label: '특허 검색', hash: 'patent-search' },
  { label: '명세서 작성', path: '/create' },
  { label: '청구항 심사', path: '/claim-review' },
] as const

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [isFeatureOpen, setIsFeatureOpen] = useState(false)

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  function handleNavClick(hash: string) {
    if (location.pathname === '/') {
      navigate(`/#${hash}`)
      requestAnimationFrame(() => document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    } else {
      navigate(`/#${hash}`)
    }
  }

  function handleLogoClick() {
    setIsFeatureOpen(false)
    if (location.pathname === '/') {
      requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
    }
  }

  return (
    <header style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 600,
      background: 'rgba(255,255,255,.95)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--lf-border)',
    }}>
      <nav style={{
        maxWidth: 1180, margin: '0 auto', padding: '0 64px',
        height: 70, display: 'flex', alignItems: 'center',
      }}>
        {/* Logo */}
        <Link to="/" onClick={handleLogoClick} style={{
          display: 'flex', alignItems: 'center', gap: 11,
          textDecoration: 'none', marginRight: 48, flexShrink: 0,
        }}>
          <span style={{
            width: 30, height: 30,
            border: '1px solid rgba(232,41,13,.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: 'var(--lf-serif)', fontSize: 10, color: 'var(--lf-gold)',
          }}>Pi</span>
          <span style={{
            fontFamily: 'var(--lf-serif)', fontSize: 15, fontWeight: 400,
            letterSpacing: '2.8px', textTransform: 'uppercase', color: 'var(--lf-navy)',
          }}>PYPI</span>
        </Link>

        {/* GNB */}
        <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          {NAV_ITEMS.map((item) => 'path' in item ? (
            <Link key={item.path} to={item.path} style={{
              fontSize: 10, fontWeight: 500, letterSpacing: '1.5px',
              textTransform: 'uppercase', color: location.pathname === item.path ? 'var(--lf-gold)' : 'var(--lf-mid)',
              padding: '0 18px', height: 70, display: 'flex', alignItems: 'center',
              transition: 'color .2s', whiteSpace: 'nowrap',
            }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-gold)')}
              onMouseLeave={e => (e.currentTarget.style.color = location.pathname === item.path ? 'var(--lf-gold)' : 'var(--lf-mid)')}
            >
              {item.label}
            </Link>
          ) : (
            <button key={item.hash} onClick={() => handleNavClick(item.hash)} style={{
              fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
              textTransform: 'uppercase', color: 'var(--lf-mid)',
              background: 'none', border: 'none', padding: '0 18px', height: 70,
              display: 'flex', alignItems: 'center', transition: 'color .2s',
              cursor: 'pointer', fontFamily: 'var(--lf-sans)', whiteSpace: 'nowrap',
            }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-navy)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-mid)')}
            >{item.label}</button>
          ))}

          {/* 기능 드롭다운 */}
          <div
            style={{ position: 'relative', height: 70 }}
            onMouseEnter={() => setIsFeatureOpen(true)}
            onMouseLeave={() => setIsFeatureOpen(false)}
          >
            <button
              type="button"
              aria-expanded={isFeatureOpen}
              onClick={() => setIsFeatureOpen(open => !open)}
              style={{
              fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
              textTransform: 'uppercase', color: isFeatureOpen ? 'var(--lf-navy)' : 'var(--lf-mid)',
              background: 'none', border: 'none', padding: '0 18px', height: 70,
              display: 'flex', alignItems: 'center', gap: 5, transition: 'color .2s',
              cursor: 'pointer', fontFamily: 'var(--lf-sans)',
              }}
            >
              기능
              <span style={{ fontSize: 8, transform: isFeatureOpen ? 'rotate(180deg)' : 'none', transition: 'transform .2s' }}>▾</span>
            </button>

            {isFeatureOpen && (
              <div style={{
                position: 'absolute', top: 70, left: 0, width: 200,
                background: 'var(--lf-bg)', border: '1px solid var(--lf-border)',
                boxShadow: '0 18px 40px -16px rgba(33,27,23,.18)', padding: '8px 0',
              }}>
                {FEATURE_LINKS.map(item => 'path' in item ? (
                  <Link
                    key={item.label}
                    to={item.path}
                    onClick={() => setIsFeatureOpen(false)}
                    style={{
                      display: 'block', padding: '12px 22px', fontSize: 13, fontWeight: 500,
                      color: 'var(--lf-navy)', textDecoration: 'none', transition: 'background .15s',
                      fontFamily: 'var(--lf-sans)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--lf-bg2)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'none')}
                  >{item.label}</Link>
                ) : (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() => {
                      setIsFeatureOpen(false)
                      handleNavClick(item.hash)
                    }}
                    style={{
                      display: 'block', width: '100%', padding: '12px 22px', fontSize: 13, fontWeight: 500,
                      color: 'var(--lf-navy)', background: 'none', border: 'none', textAlign: 'left',
                      cursor: 'pointer', transition: 'background .15s', fontFamily: 'var(--lf-sans)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--lf-bg2)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'none')}
                  >{item.label}</button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Auth */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {user ? (
            <>
              <Link to="/dashboard" style={{
                fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
                textTransform: 'uppercase', color: 'var(--lf-gold)', textDecoration: 'none',
              }}>대시보드</Link>
              <Link to="/mypage" style={{
                fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
                textTransform: 'uppercase', color: 'var(--lf-mid)', textDecoration: 'none',
              }}>마이페이지</Link>
              <button onClick={handleLogout} style={{
                fontSize: 10, fontWeight: 500, letterSpacing: '1.8px', textTransform: 'uppercase',
                color: 'var(--lf-mid)', background: 'none', border: '1px solid var(--lf-border)',
                padding: '5px 14px', cursor: 'pointer', fontFamily: 'var(--lf-sans)', transition: 'color .2s, border-color .2s',
              }}
                onMouseEnter={e => { e.currentTarget.style.color = '#e57373'; e.currentTarget.style.borderColor = 'rgba(239,68,68,.4)' }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--lf-mid)'; e.currentTarget.style.borderColor = 'var(--lf-border)' }}
              >로그아웃</button>
            </>
          ) : (
            <>
              <Link to="/login" style={{
                fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
                textTransform: 'uppercase', color: 'var(--lf-mid)', textDecoration: 'none', transition: 'color .2s',
              }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-navy)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-mid)')}
              >로그인</Link>
              <Link to="/signup" style={{
                fontSize: 10, fontWeight: 500, letterSpacing: '1.8px', textTransform: 'uppercase',
                color: '#fff', background: 'var(--lf-dark)', padding: '6px 16px',
                textDecoration: 'none', transition: 'background .2s',
              }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--lf-dark-lt)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--lf-dark)')}
              >회원가입</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
