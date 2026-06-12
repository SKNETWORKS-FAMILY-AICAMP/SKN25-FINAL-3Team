import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { pipelineApi, projectStore, StoredProject } from '../api/pipeline'

const STATUS_LABELS: Record<string, string> = {
  running: 'AI 처리중',
  completed: '완료',
  failed: '실패',
  wait_user: '입력 대기',
}

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-amber-400/20 text-amber-300 border border-amber-500/30',
  completed: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  failed: 'bg-red-500/20 text-red-400 border border-red-500/30',
  wait_user: 'bg-sky-400/20 text-sky-300 border border-sky-500/30',
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<StoredProject[]>([])
  const [deleteMode, setDeleteMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  useEffect(() => {
    setProjects(projectStore.list())
  }, [])

  // 실행중인 프로젝트 상태 동기화
  useEffect(() => {
    const running = projects.filter(p => p.status === 'running')
    if (running.length === 0) return

    const timers = running.map(p =>
      setInterval(async () => {
        try {
          const run = await pipelineApi.getRun(p.run_id)
          if (run.status !== 'running') {
            projectStore.updateStatus(p.run_id, run.status)
            setProjects(projectStore.list())
          }
        } catch {
          // ignore
        }
      }, 5000)
    )
    return () => timers.forEach(clearInterval)
  }, [projects])

  function toggleSelect(id: string) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function handleDeleteSelected() {
    if (!confirm(`선택한 ${selected.size}개 프로젝트를 삭제하시겠습니까?`)) return
    selected.forEach(id => projectStore.remove(id))
    setProjects(projectStore.list())
    setDeleteMode(false)
    setSelected(new Set())
  }

  function handleDeleteOne(id: string) {
    if (!confirm('이 프로젝트를 삭제하시겠습니까?')) return
    projectStore.remove(id)
    setProjects(projectStore.list())
  }

  return (
    <div className="pt-[70px] min-h-screen">
      <div className="max-w-5xl mx-auto px-8 py-12">
        {/* Header row */}
        <div className="flex justify-between items-center border-b border-slate-700 pb-6 mb-8">
          <h1 className="text-3xl font-bold">내 특허 프로젝트</h1>
          <div className="flex gap-3">
            {!deleteMode ? (
              <>
                <Link to="/create" className="btn-primary">
                  + 새 프로젝트
                </Link>
                {projects.length > 0 && (
                  <button onClick={() => setDeleteMode(true)} className="btn-secondary text-sm">
                    선택 삭제
                  </button>
                )}
              </>
            ) : (
              <>
                <button
                  onClick={handleDeleteSelected}
                  disabled={selected.size === 0}
                  className="btn-danger disabled:opacity-40"
                >
                  삭제 ({selected.size}개)
                </button>
                <button
                  onClick={() => { setDeleteMode(false); setSelected(new Set()) }}
                  className="btn-secondary text-sm"
                >
                  취소
                </button>
              </>
            )}
          </div>
        </div>

        {/* Project list */}
        {projects.length === 0 ? (
          <div className="card text-center py-20">
            <p className="text-slate-400 text-lg mb-6">아직 진행 중인 프로젝트가 없습니다.</p>
            <Link to="/create" className="btn-primary inline-block">
              첫 번째 특허 프로젝트 시작하기
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {deleteMode && (
              <label className="flex items-center gap-3 text-slate-300 cursor-pointer mb-2 ml-1">
                <input
                  type="checkbox"
                  className="w-4 h-4 accent-sky-400"
                  checked={selected.size === projects.length}
                  onChange={e =>
                    setSelected(e.target.checked ? new Set(projects.map(p => p.run_id)) : new Set())
                  }
                />
                전체 선택
              </label>
            )}

            {projects.map(project => (
              <div key={project.run_id} className="card flex items-center gap-4">
                {deleteMode && (
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-sky-400 shrink-0"
                    checked={selected.has(project.run_id)}
                    onChange={() => toggleSelect(project.run_id)}
                  />
                )}

                <div className="flex-1 min-w-0">
                  <Link
                    to={`/workstation/${project.run_id}`}
                    className="text-sky-400 hover:text-sky-300 font-semibold text-lg block mb-1 truncate"
                  >
                    {project.title}
                  </Link>
                  <p className="text-slate-500 text-sm">
                    생성일: {new Date(project.created_at).toLocaleDateString('ko-KR')}
                  </p>
                </div>

                <span
                  className={`shrink-0 text-sm font-semibold px-3 py-1 rounded-full ${STATUS_COLORS[project.status] ?? 'bg-slate-700 text-slate-300'}`}
                >
                  {STATUS_LABELS[project.status] ?? project.status}
                </span>

                {!deleteMode && (
                  <button
                    onClick={() => handleDeleteOne(project.run_id)}
                    className="shrink-0 text-slate-500 hover:text-red-400 transition-colors text-sm cursor-pointer"
                  >
                    삭제
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
