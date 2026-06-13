import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { pipelineApi, projectStore, StoredProject } from '../api/pipeline'

const STATUS_LABELS: Record<string, string> = {
  running: 'AI 처리중', completed: '완료', failed: '실패', wait_user: '입력 대기',
}
const STATUS_BORDER: Record<string, string> = {
  running: 'rgba(251,191,36,.5)', completed: 'rgba(52,211,153,.5)', failed: 'rgba(239,68,68,.5)', wait_user: 'rgba(154,120,64,.5)',
}
const STATUS_COLOR: Record<string, string> = {
  running: '#f59e0b', completed: '#10b981', failed: '#ef4444', wait_user: 'var(--lf-gold)',
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<StoredProject[]>([])
  const [deleteMode, setDeleteMode] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  useEffect(() => { setProjects(projectStore.list()) }, [])

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
        } catch { /* ignore */ }
      }, 5000)
    )
    return () => timers.forEach(clearInterval)
  }, [projects])

  function toggleSelect(id: string) {
    setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  }
  function handleDeleteSelected() {
    if (!confirm(`선택한 ${selected.size}개 프로젝트를 삭제하시겠습니까?`)) return
    selected.forEach(id => projectStore.remove(id))
    setProjects(projectStore.list()); setDeleteMode(false); setSelected(new Set())
  }
  function handleDeleteOne(id: string) {
    if (!confirm('이 프로젝트를 삭제하시겠습니까?')) return
    projectStore.remove(id); setProjects(projectStore.list())
  }

  return (
    <div className="page-wrap">
      <div style={{ maxWidth: 1180, margin: '0 auto', padding: '64px 64px' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--lf-border)', paddingBottom: 32, marginBottom: 48 }}>
          <div>
            <span className="label" style={{ marginBottom: 12 }}>My Projects</span>
            <h1 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(28px,3vw,36px)', fontWeight: 300, color: 'var(--lf-navy)', letterSpacing: -.4, margin: 0 }}>내 특허 프로젝트</h1>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {!deleteMode ? (
              <>
                <Link to="/create" className="btn-fill">+ 새 프로젝트</Link>
                {projects.length > 0 && <button onClick={() => setDeleteMode(true)} className="btn-line">선택 삭제</button>}
              </>
            ) : (
              <>
                <button onClick={handleDeleteSelected} disabled={selected.size === 0} className="btn-danger">삭제 ({selected.size}개)</button>
                <button onClick={() => { setDeleteMode(false); setSelected(new Set()) }} className="btn-line">취소</button>
              </>
            )}
          </div>
        </div>

        {/* List */}
        {projects.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '80px 40px' }}>
            <p style={{ color: 'var(--lf-muted)', fontSize: 14, fontWeight: 300, marginBottom: 32 }}>아직 진행 중인 프로젝트가 없습니다.</p>
            <Link to="/create" className="btn-fill">첫 번째 특허 프로젝트 시작하기 →</Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 1, border: '1px solid var(--lf-border)', background: 'var(--lf-border)' }}>
            {deleteMode && (
              <label style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 32px', background: 'var(--lf-bg2)', fontSize: 12, color: 'var(--lf-mid)', cursor: 'pointer' }}>
                <input type="checkbox" style={{ accentColor: 'var(--lf-gold)', width: 14, height: 14 }}
                  checked={selected.size === projects.length}
                  onChange={e => setSelected(e.target.checked ? new Set(projects.map(p => p.run_id)) : new Set())}
                /> 전체 선택
              </label>
            )}
            {projects.map((project, i) => (
              <div key={project.run_id} style={{
                display: 'flex', alignItems: 'center', gap: 20, padding: '28px 32px',
                background: 'var(--lf-bg)', borderLeft: `3px solid ${STATUS_BORDER[project.status] ?? 'var(--lf-border)'}`,
              }}>
                {deleteMode && (
                  <input type="checkbox" style={{ accentColor: 'var(--lf-gold)', width: 14, height: 14, flexShrink: 0 }}
                    checked={selected.has(project.run_id)} onChange={() => toggleSelect(project.run_id)} />
                )}
                <span style={{ fontFamily: 'Courier New, monospace', fontSize: 11, color: 'var(--lf-gold)', opacity: .5, flexShrink: 0, letterSpacing: 1 }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <Link to={`/workstation/${project.run_id}`} style={{ fontFamily: 'var(--lf-serif)', fontSize: 18, fontWeight: 400, color: 'var(--lf-navy)', display: 'block', marginBottom: 4, transition: 'color .2s' }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-gold)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-navy)')}
                  >{project.title}</Link>
                  <p style={{ fontSize: 11, color: 'var(--lf-muted)', letterSpacing: .5 }}>생성일: {new Date(project.created_at).toLocaleDateString('ko-KR')}</p>
                </div>
                <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: STATUS_COLOR[project.status] ?? 'var(--lf-muted)', flexShrink: 0 }}>
                  {STATUS_LABELS[project.status] ?? project.status}
                </span>
                {!deleteMode && (
                  <button onClick={() => handleDeleteOne(project.run_id)} style={{ flexShrink: 0, fontSize: 10, letterSpacing: '1px', textTransform: 'uppercase', color: 'var(--lf-muted)', background: 'none', border: 'none', cursor: 'pointer', transition: 'color .2s' }}
                    onMouseEnter={e => (e.currentTarget.style.color = '#ef4444')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-muted)')}
                  >삭제</button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
