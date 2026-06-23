import { FormEvent, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string })?.from ?? '/dashboard'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--lf-bg2)', padding: '0 24px' }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Link to="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
            <span style={{ width: 28, height: 28, border: '1px solid rgba(154,120,64,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--lf-serif)', fontSize: 9, color: 'var(--lf-gold)' }}>Pi</span>
            <span style={{ fontFamily: 'var(--lf-serif)', fontSize: 14, letterSpacing: '2.8px', textTransform: 'uppercase', color: 'var(--lf-navy)' }}>PYPI</span>
          </Link>
        </div>

        <div className="card">
          <div style={{ marginBottom: 32 }}>
            <span className="label">Account Access</span>
            <h1 className="section-title" style={{ margin:0 }}>로그인</h1>
          </div>

          {error && (
            <div style={{ background: 'rgba(239,68,68,.06)', border: '1px solid rgba(239,68,68,.3)', color: '#ef4444', padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            <div>
              <label className="label">아이디</label>
              <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="아이디를 입력하세요" required className="input-field" />
            </div>
            <div>
              <label className="label">비밀번호</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="비밀번호를 입력하세요" required className="input-field" />
            </div>
            <button type="submit" disabled={isLoading} className="btn-fill" style={{ marginTop: 8, opacity: isLoading ? .6 : 1 }}>
              {isLoading ? '로그인 중...' : '로그인 →'}
            </button>
          </form>

          <p className="muted-text" style={{ textAlign: 'center', marginTop: 28, borderTop: '1px solid var(--lf-border)', paddingTop: 24 }}>
            계정이 없으신가요?{' '}
            <Link to="/signup" style={{ color: 'var(--lf-gold)', fontWeight: 500 }}>회원가입</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
