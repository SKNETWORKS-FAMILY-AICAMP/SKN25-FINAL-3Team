import { FormEvent, useEffect, useRef, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../api/auth'
import { projectStore, StoredProject } from '../api/pipeline'

const STATUS_LABEL: Record<string, string> = {
  running: 'AI 처리중', completed: '완료', wait_user: '입력 대기', failed: '실패',
}
const STATUS_COLOR: Record<string, string> = {
  running: '#f59e0b', completed: '#10b981', wait_user: 'var(--lf-gold)', failed: '#ef4444',
}

export default function MyPage() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<StoredProject[]>([])
  const [saveMsg, setSaveMsg] = useState('')
  const [saveErr, setSaveErr] = useState('')
  const nameRef = useRef<HTMLInputElement>(null)
  const emailRef = useRef<HTMLInputElement>(null)

  useEffect(() => { setProjects(projectStore.list()) }, [])

  const stats = {
    total: projects.length,
    running: projects.filter(p => p.status === 'running').length,
    completed: projects.filter(p => p.status === 'completed').length,
    failed: projects.filter(p => p.status === 'failed').length,
    wait_user: projects.filter(p => p.status === 'wait_user').length,
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    setSaveErr('')
    try {
      await authApi.updateProfile({
        name:  nameRef.current?.value  || undefined,
        email: emailRef.current?.value || undefined,
      })
      setSaveMsg('저장되었습니다.')
      setTimeout(() => setSaveMsg(''), 2500)
    } catch (err) {
      setSaveErr(err instanceof Error ? err.message : '저장에 실패했습니다.')
    }
  }

  if (!user) return null

  return (
    <div className="page-wrap">
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '64px 64px' }}>
        {/* Title */}
        <div style={{ borderBottom: '1px solid var(--lf-border)', paddingBottom: 32, marginBottom: 56 }}>
          <span className="label">My Account</span>
          <h1 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(28px,3vw,36px)', fontWeight: 300, color: 'var(--lf-navy)', letterSpacing: -.4, margin: 0 }}>마이페이지</h1>
          <p style={{ fontSize: 15, fontWeight: 300, color: 'var(--lf-mid)', marginTop: 8 }}>내 계정 정보와 특허 프로젝트 현황을 확인합니다.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: 'var(--lf-border)', border: '1px solid var(--lf-border)' }}>

          {/* Left: info + stats */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {/* User info */}
            <div style={{ background: 'var(--lf-bg)', padding: '40px' }}>
              <p className="label">회원 기본 정보</p>
              <dl style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {([['아이디', user.username], ['이름', user.name || '(지정 안 됨)'], ['이메일', user.email || '(지정 안 됨)']] as const).map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--lf-border)', paddingBottom: 12 }}>
                    <dt style={{ fontSize: 14, fontWeight: 400, color: 'var(--lf-muted)', letterSpacing: .5 }}>{k}</dt>
                    <dd style={{ fontSize: 15, fontWeight: 500, color: 'var(--lf-navy)' }}>{v}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Stats */}
            <div style={{ background: 'var(--lf-bg2)', padding: '40px' }}>
              <p className="label">프로젝트 현황</p>
              <div style={{ textAlign: 'center', padding: '24px', background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', marginBottom: 16 }}>
                <p style={{ fontSize: 13, fontWeight: 500, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--lf-muted)', marginBottom: 8 }}>총 진행 프로젝트</p>
                <p style={{ fontFamily: 'var(--lf-serif)', fontSize: 48, fontWeight: 300, color: 'var(--lf-gold)', lineHeight: 1 }}>{stats.total}</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, background: 'var(--lf-border)', border: '1px solid var(--lf-border)' }}>
                {(['running', 'completed', 'wait_user', 'failed'] as const).map(key => (
                  <div key={key} style={{ background: 'var(--lf-bg)', padding: '20px 24px' }}>
                    <p style={{ fontSize: 12, fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: STATUS_COLOR[key], marginBottom: 8 }}>{STATUS_LABEL[key]}</p>
                    <p style={{ fontFamily: 'var(--lf-serif)', fontSize: 28, fontWeight: 300, color: 'var(--lf-navy)', lineHeight: 1 }}>{stats[key]}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: edit form */}
          <div style={{ background: 'var(--lf-bg)', padding: '40px' }}>
            <p className="label">회원 정보 수정</p>
            {saveMsg && (
              <div style={{ background: 'rgba(52,211,153,.08)', border: '1px solid rgba(52,211,153,.3)', color: '#10b981', padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
                {saveMsg}
              </div>
            )}
            {saveErr && (
              <div style={{ background: 'rgba(239,68,68,.06)', border: '1px solid rgba(239,68,68,.3)', color: '#ef4444', padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
                {saveErr}
              </div>
            )}
            <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid var(--lf-border)' }}>
                <span style={{ fontSize: 13, fontWeight: 500, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--lf-muted)' }}>회원 ID</span>
                <span style={{ fontSize: 15, fontWeight: 400, color: 'var(--lf-navy)' }}>{user.username}</span>
              </div>
              <div>
                <label className="label">이름</label>
                <input ref={nameRef} type="text" defaultValue={user.name} placeholder="이름을 입력하세요" className="input-field" />
              </div>
              <div>
                <label className="label">이메일 주소</label>
                <input ref={emailRef} type="email" defaultValue={user.email} placeholder="example@email.com" className="input-field" />
              </div>
              <p style={{ fontSize: 14, fontWeight: 300, color: 'var(--lf-muted)', padding: '12px 0', borderTop: '1px solid var(--lf-border)' }}>
                비밀번호 변경은 보안 정책상 별도 절차가 필요합니다.
              </p>
              <button type="submit" className="btn-fill" style={{ alignSelf: 'flex-start' }}>저장하기</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
