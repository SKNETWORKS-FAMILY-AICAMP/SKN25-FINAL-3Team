import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    username: '',
    name: '',
    password: '',
    password2: '',
    gender: 'M',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  function update(field: keyof typeof form, value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (form.password !== form.password2) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    setError('')
    setIsLoading(true)
    try {
      await signup(form)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : '회원가입에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f172a] px-4 py-12">
      <div className="w-full max-w-md">
        <div className="card">
          <h1 className="text-2xl font-bold text-center mb-8">회원가입</h1>

          {error && (
            <div className="bg-red-500/10 border border-red-500/40 text-red-400 rounded-lg px-4 py-3 mb-6 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            <div>
              <label className="label">아이디</label>
              <input
                type="text"
                value={form.username}
                onChange={e => update('username', e.target.value)}
                placeholder="사용할 아이디"
                required
                className="input-field"
              />
            </div>

            <div>
              <label className="label">이름</label>
              <input
                type="text"
                value={form.name}
                onChange={e => update('name', e.target.value)}
                placeholder="실명 또는 닉네임"
                required
                className="input-field"
              />
            </div>

            <div>
              <label className="label">성별</label>
              <div className="flex gap-6 mt-1">
                {(['M', 'F'] as const).map(g => (
                  <label key={g} className="flex items-center gap-2 cursor-pointer text-slate-300">
                    <input
                      type="radio"
                      name="gender"
                      value={g}
                      checked={form.gender === g}
                      onChange={() => update('gender', g)}
                      className="accent-sky-400"
                    />
                    {g === 'M' ? '남성' : '여성'}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="label">비밀번호</label>
              <input
                type="password"
                value={form.password}
                onChange={e => update('password', e.target.value)}
                placeholder="8자 이상 입력"
                required
                className="input-field"
              />
            </div>

            <div>
              <label className="label">비밀번호 확인</label>
              <input
                type="password"
                value={form.password2}
                onChange={e => update('password2', e.target.value)}
                placeholder="비밀번호 재입력"
                required
                className="input-field"
              />
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary mt-2">
              {isLoading ? '처리 중...' : '가입하기'}
            </button>
          </form>

          <p className="text-center text-slate-400 text-sm mt-6">
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="text-sky-400 hover:text-sky-300">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
