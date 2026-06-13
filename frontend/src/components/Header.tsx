import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const NAV_ITEMS = [
  { label: '서비스 소개', hash: 'intro' },
  { label: 'AI 에이전트', hash: 'pipeline' },
  { label: '기능',        hash: 'features' },
] as const

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  function handleNavClick(hash: string) {
    if (location.pathname === '/') {
      document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth' })
    } else {
      navigate('/')
      setTimeout(() => document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth' }), 100)
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
        <Link to="/" style={{
          display: 'flex', alignItems: 'center', gap: 11,
          textDecoration: 'none', marginRight: 48, flexShrink: 0,
        }}>
          <span style={{
            width: 30, height: 30,
            border: '1px solid rgba(154,120,64,.4)',
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
          {NAV_ITEMS.map(({ label, hash }) => (
            <button key={hash} onClick={() => handleNavClick(hash)} style={{
              fontSize: 10, fontWeight: 500, letterSpacing: '1.8px',
              textTransform: 'uppercase', color: 'var(--lf-mid)',
              background: 'none', border: 'none', padding: '0 18px', height: 70,
              display: 'flex', alignItems: 'center', transition: 'color .2s',
              cursor: 'pointer', fontFamily: 'var(--lf-sans)',
            }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-navy)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-mid)')}
            >{label}</button>
          ))}
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
                color: '#fff', background: 'var(--lf-navy)', padding: '6px 16px',
                textDecoration: 'none', transition: 'background .2s',
              }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--lf-gold)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--lf-navy)')}
              >회원가입</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
