import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ username: '', name: '', age: '', password: '', password2: '', gender: 'M' })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  function update(field: keyof typeof form, value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (form.password !== form.password2) { setError('비밀번호가 일치하지 않습니다.'); return }
    setError('')
    setIsLoading(true)
    try {
      await signup({ ...form, age: form.age ? Number(form.age) : undefined })
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '회원가입에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--lf-bg2)', padding: '80px 24px' }}>
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
            <span className="label">New Account</span>
            <h1 style={{ fontFamily: 'var(--lf-serif)', fontSize: 28, fontWeight: 300, color: 'var(--lf-navy)', margin: 0 }}>회원가입</h1>
          </div>

          {error && (
            <div style={{ background: 'rgba(239,68,68,.06)', border: '1px solid rgba(239,68,68,.3)', color: '#ef4444', padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            <div>
              <label className="label">아이디</label>
              <input type="text" value={form.username} onChange={e => update('username', e.target.value)} placeholder="사용할 아이디" required className="input-field" />
            </div>
            <div>
              <label className="label">이름</label>
              <input type="text" value={form.name} onChange={e => update('name', e.target.value)} placeholder="실명 또는 닉네임" required className="input-field" />
            </div>
            <div>
              <label className="label">나이</label>
              <input type="number" value={form.age} onChange={e => update('age', e.target.value)} placeholder="나이를 입력하세요" required min={1} max={150} className="input-field" />
            </div>
            <div>
              <label className="label">성별</label>
              <div style={{ display: 'flex', gap: 32, marginTop: 8 }}>
                {(['M', 'F'] as const).map(g => (
                  <label key={g} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: form.gender === g ? 'var(--lf-navy)' : 'var(--lf-mid)' }}>
                    <input type="radio" name="gender" value={g} checked={form.gender === g} onChange={() => update('gender', g)} style={{ accentColor: 'var(--lf-gold)' }} />
                    {g === 'M' ? '남성' : '여성'}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="label">비밀번호</label>
              <input type="password" value={form.password} onChange={e => update('password', e.target.value)} placeholder="8자 이상 입력" required className="input-field" />
            </div>
            <div>
              <label className="label">비밀번호 확인</label>
              <input type="password" value={form.password2} onChange={e => update('password2', e.target.value)} placeholder="비밀번호 재입력" required className="input-field" />
            </div>
            <button type="submit" disabled={isLoading} className="btn-fill" style={{ marginTop: 8, opacity: isLoading ? .6 : 1 }}>
              {isLoading ? '처리 중...' : '가입하기 →'}
            </button>
          </form>

          <p style={{ textAlign: 'center', fontSize: 12, fontWeight: 300, color: 'var(--lf-muted)', marginTop: 28, borderTop: '1px solid var(--lf-border)', paddingTop: 24 }}>
            이미 계정이 있으신가요?{' '}
            <Link to="/login" style={{ color: 'var(--lf-gold)', fontWeight: 500 }}>로그인</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
