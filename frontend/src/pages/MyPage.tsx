import { FormEvent, useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { projectStore, StoredProject } from '../api/pipeline'

const STATUS_COLORS: Record<string, string> = {
  running: 'text-amber-400',
  completed: 'text-emerald-400',
  failed: 'text-red-400',
  wait_user: 'text-sky-400',
}

export default function MyPage() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<StoredProject[]>([])
  const [saveMsg, setSaveMsg] = useState('')

  useEffect(() => {
    setProjects(projectStore.list())
  }, [])

  const stats = {
    total: projects.length,
    running: projects.filter(p => p.status === 'running').length,
    completed: projects.filter(p => p.status === 'completed').length,
    failed: projects.filter(p => p.status === 'failed').length,
    wait_user: projects.filter(p => p.status === 'wait_user').length,
  }

  function handleSave(e: FormEvent) {
    e.preventDefault()
    // 실제 PATCH /auth/api/auth/me/ 연동 가능 — 현재 Django 미구현
    setSaveMsg('저장되었습니다.')
    setTimeout(() => setSaveMsg(''), 2500)
  }

  if (!user) return null

  return (
    <div className="pt-[70px] min-h-screen">
      <div className="max-w-5xl mx-auto px-8 py-12">
        <h1 className="text-3xl font-bold text-center text-sky-400 mb-2">마이페이지</h1>
        <p className="text-center text-slate-400 mb-12">내 계정 정보와 특허 프로젝트 현황을 확인합니다.</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: info + stats */}
          <div className="flex flex-col gap-6">
            {/* User info */}
            <div className="card">
              <h3 className="text-sky-400 font-bold mb-5 text-lg border-b border-slate-700 pb-3">
                👤 회원 기본 정보
              </h3>
              <dl className="flex flex-col gap-3 text-sm">
                {[
                  ['아이디', user.username],
                  ['이름', user.name || '(지정 안 됨)'],
                  ['이메일', user.email || '(지정 안 됨)'],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <dt className="text-slate-400">{k}</dt>
                    <dd className="font-semibold">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Stats */}
            <div className="card">
              <h3 className="text-emerald-400 font-bold mb-5 text-lg border-b border-slate-700 pb-3">
                📋 특허 프로젝트 현황
              </h3>
              <div className="bg-[#0f172a] rounded-xl text-center p-5 mb-5">
                <p className="text-slate-400 text-sm mb-1">총 진행 프로젝트</p>
                <p className="text-emerald-400 text-4xl font-bold">
                  {stats.total} <span className="text-lg font-normal">개</span>
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'AI 처리중', key: 'running', color: 'border-amber-500' },
                  { label: '완료', key: 'completed', color: 'border-emerald-500' },
                  { label: '입력 대기', key: 'wait_user', color: 'border-sky-500' },
                  { label: '실패', key: 'failed', color: 'border-red-500' },
                ].map(({ label, key, color }) => (
                  <div key={key} className={`bg-[#111827] p-4 rounded-xl border-l-4 ${color}`}>
                    <p className={`text-xs mb-1 ${STATUS_COLORS[key]}`}>{label}</p>
                    <p className="text-xl font-bold">{stats[key as keyof typeof stats]} 개</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: edit form */}
          <div className="card">
            <h3 className="text-slate-300 font-bold mb-5 text-lg border-b border-slate-700 pb-3">
              ⚙️ 회원 정보 수정
            </h3>

            {saveMsg && (
              <div className="bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 rounded-lg px-4 py-2 mb-5 text-sm">
                {saveMsg}
              </div>
            )}

            <form onSubmit={handleSave} className="flex flex-col gap-5">
              <div className="flex justify-between items-center bg-[#0f172a] px-4 py-3 rounded-xl">
                <span className="text-slate-400 text-sm">회원 ID</span>
                <span className="text-slate-200 font-semibold text-sm">{user.username}</span>
              </div>

              <div>
                <label className="label">이름</label>
                <input
                  type="text"
                  defaultValue={user.name}
                  placeholder="이름을 입력하세요"
                  className="input-field"
                />
              </div>

              <div>
                <label className="label">이메일 주소</label>
                <input
                  type="email"
                  defaultValue={user.email}
                  placeholder="example@email.com"
                  className="input-field"
                />
              </div>

              <div className="bg-[#0f172a] rounded-xl px-4 py-3 text-sm text-slate-500">
                비밀번호 변경은 보안 정책상 별도 절차가 필요합니다.
              </div>

              <button type="submit" className="btn-primary">저장하기</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
