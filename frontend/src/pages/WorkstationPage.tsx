import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { pipelineApi, PatentRun, RunResult, projectStore } from '../api/pipeline'

const AGENT_LABELS: Record<string, string> = {
  parse: '발명 파싱',
  summary: 'AI 요약',
  priorart: '선행기술 검색',
  claim: '청구항 작성',
  drawing: '도면 생성',
  specification: '명세서 작성',
  critic: '품질 검토',
}

export default function WorkstationPage() {
  const { runId } = useParams<{ runId: string }>()
  const [run, setRun] = useState<PatentRun | null>(null)
  const [runResult, setRunResult] = useState<RunResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isContinuing, setIsContinuing] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 로컬 프로젝트 메타
  const storedProject = runId ? projectStore.list().find(p => p.run_id === runId) : undefined

  async function fetchRun() {
    if (!runId) return
    try {
      const data = await pipelineApi.getRun(runId)
      setRun(data)
      if (data.status !== 'running') {
        if (pollRef.current) clearInterval(pollRef.current)
        projectStore.updateStatus(runId, data.status)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '실행 정보를 불러올 수 없습니다.')
    }
  }

  useEffect(() => {
    if (!runId) return
    setIsLoading(true)
    fetchRun().finally(() => setIsLoading(false))
  }, [runId])

  // 실행 중이면 폴링
  useEffect(() => {
    if (run?.status === 'running') {
      pollRef.current = setInterval(fetchRun, 4000)
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [run?.status])

  async function handleContinue(userInput?: string) {
    if (!runResult) return
    setIsContinuing(true)
    try {
      const result = await pipelineApi.continue(runResult.state, userInput)
      setRunResult(result)
      await fetchRun()
    } catch (err) {
      setError(err instanceof Error ? err.message : '계속 실행에 실패했습니다.')
    } finally {
      setIsContinuing(false)
    }
  }

  if (isLoading) {
    return (
      <div className="pt-[70px] flex items-center justify-center h-screen text-slate-400">
        <span className="animate-pulse">로딩 중...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="pt-[70px] flex flex-col items-center justify-center h-screen gap-4">
        <p className="text-red-400">{error}</p>
        <Link to="/dashboard" className="btn-secondary text-sm">대시보드로 돌아가기</Link>
      </div>
    )
  }

  if (!run) return null

  const state = runResult?.state ?? {}
  const claims: string[] = (state.claims as string[]) ?? []
  const specification: string = (state.specification as string) ?? ''
  const priorArt: string = (state.prior_art_summary as string) ?? ''

  return (
    <div className="pt-[70px] min-h-screen bg-[#0f172a]">
      {/* Top bar */}
      <div className="border-b border-slate-800 px-8 py-4 flex items-center justify-between bg-slate-900">
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-slate-400 hover:text-white text-sm">← 대시보드</Link>
          <span className="text-slate-600">/</span>
          <h1 className="text-lg font-semibold text-white">
            {storedProject?.title ?? runId}
          </h1>
        </div>
        <StatusBadge status={run.status} />
      </div>

      <div className="flex h-[calc(100vh-70px-65px)]">
        {/* Left panel: run info */}
        <div className="w-80 border-r border-slate-800 bg-slate-900 overflow-y-auto p-6 flex flex-col gap-6">
          {/* Progress */}
          <div>
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">파이프라인 진행</h3>
            <div className="flex flex-col gap-2">
              {run.completed_agents.map(agent => (
                <div key={agent} className="flex items-center gap-2 text-sm">
                  <span className="text-emerald-400">✓</span>
                  <span className="text-slate-300">{AGENT_LABELS[agent] ?? agent}</span>
                </div>
              ))}
              {run.status === 'running' && run.current_agent && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-amber-400 animate-spin">⟳</span>
                  <span className="text-amber-300">{AGENT_LABELS[run.current_agent] ?? run.current_agent}</span>
                </div>
              )}
            </div>
          </div>

          {/* User input */}
          <div>
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">발명 설명</h3>
            <pre className="text-xs text-slate-400 whitespace-pre-wrap leading-relaxed bg-[#0f172a] rounded-lg p-3 max-h-60 overflow-y-auto">
              {run.user_input}
            </pre>
          </div>

          {/* Errors */}
          {run.errors.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-red-400 uppercase tracking-wider mb-3">오류</h3>
              {run.errors.map((e, i) => (
                <p key={i} className="text-xs text-red-400 mb-1">{e}</p>
              ))}
            </div>
          )}
        </div>

        {/* Right panel: results */}
        <div className="flex-1 overflow-y-auto p-8">
          {run.status === 'running' ? (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4">
              <div className="text-5xl animate-pulse">🤖</div>
              <h2 className="text-xl font-bold text-sky-400">AI 분석 진행 중</h2>
              <p className="text-slate-400">
                현재 단계:{' '}
                <span className="text-amber-300 font-semibold">
                  {AGENT_LABELS[run.current_agent ?? ''] ?? run.current_agent ?? '준비 중'}
                </span>
              </p>
              <p className="text-slate-500 text-sm">완료 시 자동으로 결과가 표시됩니다.</p>
            </div>
          ) : (
            <ResultPanel
              claims={claims}
              specification={specification}
              priorArt={priorArt}
              state={state}
              status={run.status}
              isContinuing={isContinuing}
              onContinue={handleContinue}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    running: 'bg-amber-400/20 text-amber-300 border-amber-500/30',
    completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    wait_user: 'bg-sky-400/20 text-sky-300 border-sky-500/30',
  }
  const labels: Record<string, string> = {
    running: 'AI 처리중',
    completed: '완료',
    failed: '실패',
    wait_user: '입력 대기',
  }
  return (
    <span className={`text-sm font-semibold px-3 py-1 rounded-full border ${map[status] ?? 'bg-slate-700 text-slate-300'}`}>
      {labels[status] ?? status}
    </span>
  )
}

function ResultPanel({
  claims, specification, priorArt, state, status, isContinuing, onContinue,
}: {
  claims: string[]
  specification: string
  priorArt: string
  state: Record<string, unknown>
  status: string
  isContinuing: boolean
  onContinue: (input?: string) => void
}) {
  const [tab, setTab] = useState<'claims' | 'spec' | 'priorart' | 'raw'>('claims')

  const tabs = [
    { id: 'claims', label: '청구항', count: claims.length },
    { id: 'spec', label: '명세서', count: specification ? 1 : 0 },
    { id: 'priorart', label: '선행기술', count: priorArt ? 1 : 0 },
    { id: 'raw', label: 'Raw 상태', count: null },
  ] as const

  return (
    <div className="flex flex-col gap-6">
      {status === 'wait_user' && (
        <div className="card border-sky-500/40 bg-sky-500/5">
          <p className="text-sky-300 font-semibold mb-3">추가 입력이 필요합니다</p>
          <button
            onClick={() => onContinue()}
            disabled={isContinuing}
            className="btn-primary text-sm"
          >
            {isContinuing ? '처리 중...' : '계속 진행'}
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-700">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id as typeof tab)}
            className={`px-4 py-2 text-sm font-medium transition-colors cursor-pointer ${
              tab === t.id
                ? 'border-b-2 border-sky-400 text-sky-400 -mb-px'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {t.label}
            {t.count !== null && t.count > 0 && (
              <span className="ml-1.5 text-xs bg-slate-700 px-1.5 py-0.5 rounded-full">{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'claims' && (
        <div className="flex flex-col gap-4">
          {claims.length === 0 ? (
            <p className="text-slate-500 text-sm">청구항이 아직 생성되지 않았습니다.</p>
          ) : (
            claims.map((claim, i) => (
              <div key={i} className="card">
                <h4 className="text-sky-400 font-bold text-sm mb-2">청구항 {i + 1}</h4>
                <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{claim}</p>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'spec' && (
        <div className="card">
          {specification ? (
            <pre className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{specification}</pre>
          ) : (
            <p className="text-slate-500 text-sm">명세서가 아직 생성되지 않았습니다.</p>
          )}
        </div>
      )}

      {tab === 'priorart' && (
        <div className="card">
          {priorArt ? (
            <pre className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{priorArt}</pre>
          ) : (
            <p className="text-slate-500 text-sm">선행기술 분석이 아직 완료되지 않았습니다.</p>
          )}
        </div>
      )}

      {tab === 'raw' && (
        <div className="card">
          <pre className="text-xs text-slate-400 overflow-auto max-h-[60vh]">
            {JSON.stringify(state, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
