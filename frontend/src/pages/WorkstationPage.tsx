import { useEffect, useRef, useState } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import { pipelineApi, PatentRun, RunResult, projectStore } from '../api/pipeline'
import type { AgentRunResult } from '../api/pipeline'

const AGENT_LABELS: Record<string, string> = {
  parse: '발명 파싱', summary: 'AI 요약', priorart: '선행기술 검색',
  claim: '청구항 작성', drawing: '도면 생성', specification: '명세서 작성', critic: '품질 검토',
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  running:   { label: 'AI 처리중',  color: '#f59e0b' },
  completed: { label: '완료',       color: '#10b981' },
  failed:    { label: '실패',       color: '#ef4444' },
  wait_user: { label: '입력 대기',  color: 'var(--lf-gold)' },
}

export default function WorkstationPage() {
  const { runId } = useParams<{ runId: string }>()
  const location = useLocation()
  const [run, setRun] = useState<PatentRun | null>(null)
  const [runResult, setRunResult] = useState<RunResult | null>(
    (location.state as { runResult?: RunResult } | null)?.runResult ?? null
  )
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isContinuing, setIsContinuing] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const storedProject = runId ? projectStore.list().find(p => p.run_id === runId) : undefined

  async function fetchRun() {
    if (!runId) return
    try {
      const data = await pipelineApi.getRun(runId)
      setRun(data)
      if (data.state && Object.keys(data.state).length > 0) {
        setRunResult(prev => prev ?? { run_id: data.run_id, state: data.state!, decision: data.master_decision ?? {} })
      }
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

  useEffect(() => {
    if (run?.status === 'running') pollRef.current = setInterval(fetchRun, 4000)
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
      <div style={{ paddingTop: 70, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--lf-mid)' }}>
        <span style={{ fontSize: 12, letterSpacing: '2px', textTransform: 'uppercase' }}>Loading...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ paddingTop: 70, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: 16 }}>
        <p style={{ color: '#ef4444', fontSize: 14 }}>{error}</p>
        <Link to="/dashboard" className="btn-line" style={{ fontSize: 10 }}>대시보드로 돌아가기</Link>
      </div>
    )
  }

  if (!run) return null

  const state = runResult?.state ?? {}

  // state.claims can be:
  //   1. ClaimAgentOutput dict  → { draft_claims: [{ text: "..." }, ...], ... }
  //   2. string[]               → after local edit save
  const rawClaims = state.claims
  const claims: string[] = (() => {
    if (Array.isArray(rawClaims)) return rawClaims as string[]
    const draftClaims = (rawClaims as { draft_claims?: { text: string }[] } | null)?.draft_claims
    if (Array.isArray(draftClaims)) return draftClaims.map(d => d.text)
    return []
  })()

  // state.specification is a SpecificationAgentOutput dict or plain string (legacy)
  const rawSpec = state.specification
  const specification: string = (() => {
    if (!rawSpec) return ''
    if (typeof rawSpec === 'string') return rawSpec
    const s = rawSpec as Record<string, string>
    return [
      s.technical_field         && `[기술 분야]\n${s.technical_field}`,
      s.background_art          && `[배경 기술]\n${s.background_art}`,
      s.problem_to_solve        && `[해결하려는 과제]\n${s.problem_to_solve}`,
      s.means_for_solving       && `[과제의 해결 수단]\n${s.means_for_solving}`,
      s.effects                 && `[발명의 효과]\n${s.effects}`,
      s.detailed_description    && `[발명의 상세한 설명]\n${s.detailed_description}`,
    ].filter(Boolean).join('\n\n')
  })()

  // state.prior_art is PriorArtAgentOutput dict; state.prior_art_summary is legacy key
  const rawPriorArt = state.prior_art ?? state.prior_art_summary
  const priorArt: string = (() => {
    if (!rawPriorArt) return ''
    if (typeof rawPriorArt === 'string') return rawPriorArt
    const p = rawPriorArt as { analysis_summary?: string; candidates?: { title: string; summary: string }[] }
    const parts: string[] = []
    if (p.analysis_summary) parts.push(`[종합 분석]\n${p.analysis_summary}`)
    if (Array.isArray(p.candidates) && p.candidates.length > 0) {
      parts.push('[선행기술 후보]')
      p.candidates.forEach((c, i) => {
        parts.push(`${i + 1}. ${c.title}\n${c.summary}`)
      })
    }
    return parts.join('\n\n')
  })()
  const st = STATUS_MAP[run.status] ?? { label: run.status, color: 'var(--lf-mid)' }

  return (
    <div style={{ paddingTop: 70, minHeight: '100vh', background: 'var(--lf-bg)' }}>
      {/* Top bar */}
      <div style={{ borderBottom: '1px solid var(--lf-border)', padding: '0 40px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--lf-bg2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link to="/dashboard" style={{ fontSize: 10, fontWeight: 500, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--lf-mid)', transition: 'color .2s' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--lf-navy)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--lf-mid)')}
          >← 대시보드</Link>
          <span style={{ color: 'var(--lf-border)', fontSize: 10 }}>/</span>
          <h1 style={{ fontFamily: 'var(--lf-serif)', fontSize: 16, fontWeight: 400, color: 'var(--lf-navy)', margin: 0 }}>
            {storedProject?.title ?? runId}
          </h1>
        </div>
        <span style={{ fontSize: 9, fontWeight: 600, letterSpacing: '2px', textTransform: 'uppercase', color: st.color }}>
          ● {st.label}
        </span>
      </div>

      <div style={{ display: 'flex', height: 'calc(100vh - 70px - 56px)' }}>
        {/* Left sidebar */}
        <div style={{ width: 280, borderRight: '1px solid var(--lf-border)', background: 'var(--lf-bg2)', overflowY: 'auto', padding: 32, display: 'flex', flexDirection: 'column', gap: 32 }}>
          <div>
            <p className="label">파이프라인 진행</p>
            <div style={{ position: 'relative', borderLeft: '1px solid rgba(154,120,64,.2)', paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {run.completed_agents.map(agent => (
                <div key={agent} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--lf-body)' }}>
                  <span style={{ color: '#10b981', fontSize: 10 }}>✓</span>
                  {AGENT_LABELS[agent] ?? agent}
                </div>
              ))}
              {run.status === 'running' && run.current_agent && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#f59e0b' }}>
                  <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', fontSize: 10 }}>⟳</span>
                  {AGENT_LABELS[run.current_agent] ?? run.current_agent}
                </div>
              )}
            </div>
          </div>

          <div>
            <p className="label">발명 설명</p>
            <pre style={{ fontSize: 11, color: 'var(--lf-mid)', whiteSpace: 'pre-wrap', lineHeight: 1.8, background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', padding: 12, maxHeight: 240, overflowY: 'auto', fontFamily: 'var(--lf-sans)' }}>
              {run.user_input}
            </pre>
          </div>

          {run.errors.length > 0 && (
            <div>
              <p className="label" style={{ color: '#ef4444' }}>오류</p>
              {run.errors.map((e, i) => <p key={i} style={{ fontSize: 11, color: '#ef4444', marginBottom: 4 }}>{e}</p>)}
            </div>
          )}
        </div>

        {/* Right panel */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 40 }}>
          {run.status === 'running' ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', gap: 16 }}>
              <div style={{ width: 48, height: 48, border: '2px solid var(--lf-gold)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
              <h2 style={{ fontFamily: 'var(--lf-serif)', fontSize: 24, fontWeight: 300, color: 'var(--lf-navy)' }}>AI 분석 진행 중</h2>
              <p style={{ fontSize: 13, color: 'var(--lf-mid)' }}>
                현재 단계: <span style={{ color: '#f59e0b', fontWeight: 500 }}>{AGENT_LABELS[run.current_agent ?? ''] ?? run.current_agent ?? '준비 중'}</span>
              </p>
              <p style={{ fontSize: 12, color: 'var(--lf-muted)' }}>완료 시 자동으로 결과가 표시됩니다.</p>
            </div>
          ) : (
            <ResultPanel
              claims={claims} specification={specification} priorArt={priorArt}
              state={state} status={run.status} isContinuing={isContinuing}
              onContinue={handleContinue}
              onStateUpdate={(newState) => setRunResult(r => r ? { ...r, state: newState } : { run_id: runId ?? '', state: newState, decision: {} })}
            />
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

function ResultPanel({ claims, specification, priorArt, state, status, isContinuing, onContinue, onStateUpdate }: {
  claims: string[]; specification: string; priorArt: string; state: Record<string, unknown>;
  status: string; isContinuing: boolean
  onContinue: (input?: string) => void
  onStateUpdate: (newState: Record<string, unknown>) => void
}) {
  const [tab, setTab] = useState<'claims' | 'spec' | 'priorart' | 'raw'>('claims')
  const [isGenerating, setIsGenerating] = useState(false)
  const [genError, setGenError] = useState('')
  const [editMode, setEditMode] = useState(false)
  const [editedClaims, setEditedClaims] = useState<string[]>([])

  function startEdit() {
    setEditedClaims([...claims])
    setEditMode(true)
  }

  function saveEdit() {
    onStateUpdate({ ...state, claims: editedClaims })
    setEditMode(false)
  }

  async function generateClaims() {
    setIsGenerating(true)
    setGenError('')
    try {
      const result: AgentRunResult = await pipelineApi.runAgent('claim', state)
      onStateUpdate(result.state)
    } catch (err) {
      setGenError(err instanceof Error ? err.message : '청구항 생성에 실패했습니다.')
    } finally {
      setIsGenerating(false)
    }
  }

  const tabs = [
    { id: 'claims',  label: '청구항',   count: claims.length },
    { id: 'spec',    label: '명세서',   count: specification ? 1 : 0 },
    { id: 'priorart',label: '선행기술', count: priorArt ? 1 : 0 },
    { id: 'raw',     label: 'Raw 상태', count: null },
  ] as const

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {status === 'wait_user' && (
        <div style={{ background: 'rgba(154,120,64,.06)', border: '1px solid rgba(154,120,64,.3)', padding: '20px 24px' }}>
          <p style={{ fontFamily: 'var(--lf-serif)', fontSize: 16, color: 'var(--lf-navy)', marginBottom: 12 }}>추가 입력이 필요합니다</p>
          <button onClick={() => onContinue()} disabled={isContinuing} className="btn-gold" style={{ opacity: isContinuing ? .6 : 1 }}>
            {isContinuing ? '처리 중...' : '계속 진행 →'}
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--lf-border)', gap: 0 }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id as typeof tab)} style={{
            padding: '10px 20px', fontSize: 10, fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase',
            color: tab === t.id ? 'var(--lf-gold)' : 'var(--lf-mid)',
            background: 'none', border: 'none', borderBottom: tab === t.id ? '2px solid var(--lf-gold)' : '2px solid transparent',
            cursor: 'pointer', fontFamily: 'var(--lf-sans)', transition: 'color .2s', marginBottom: -1,
          }}>
            {t.label}
            {t.count !== null && t.count > 0 && (
              <span style={{ marginLeft: 6, fontSize: 9, fontFamily: 'Courier New, monospace', color: 'var(--lf-gold)', opacity: .7 }}>{t.count}</span>
            )}
          </button>
        ))}
      </div>

      {tab === 'claims' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Action bar */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button onClick={generateClaims} disabled={isGenerating} className="btn-fill" style={{ fontSize: 10, padding: '8px 16px', opacity: isGenerating ? .6 : 1 }}>
              {isGenerating ? '⟳ 생성 중...' : claims.length > 0 ? '청구항 재작성' : '청구항 작성'}
            </button>
            {claims.length > 0 && !editMode && (
              <button onClick={startEdit} className="btn-line" style={{ fontSize: 10, padding: '8px 16px' }}>청구항 수정</button>
            )}
            {editMode && (
              <>
                <button onClick={saveEdit} className="btn-gold" style={{ fontSize: 10, padding: '8px 16px' }}>저장</button>
                <button onClick={() => setEditMode(false)} className="btn-line" style={{ fontSize: 10, padding: '8px 16px' }}>취소</button>
              </>
            )}
            {genError && <span style={{ fontSize: 11, color: '#ef4444' }}>{genError}</span>}
          </div>

          {isGenerating ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '32px 28px', border: '1px solid var(--lf-border)', background: 'var(--lf-bg)' }}>
              <div style={{ width: 20, height: 20, border: '2px solid var(--lf-gold)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', flexShrink: 0 }} />
              <p style={{ fontSize: 13, color: 'var(--lf-mid)', fontWeight: 300 }}>AI가 청구항을 작성하고 있습니다...</p>
            </div>
          ) : claims.length === 0 ? (
            <div style={{ background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', padding: '40px 28px', textAlign: 'center' }}>
              <p style={{ color: 'var(--lf-muted)', fontSize: 13, marginBottom: 4 }}>청구항이 아직 생성되지 않았습니다.</p>
              <p style={{ color: 'var(--lf-muted)', fontSize: 11 }}>위의 "청구항 작성" 버튼을 눌러 AI가 청구항을 생성하도록 하세요.</p>
            </div>
          ) : editMode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1, border: '1px solid var(--lf-border)', background: 'var(--lf-border)' }}>
              {editedClaims.map((claim, i) => (
                <div key={i} style={{ background: 'var(--lf-bg)', padding: '24px 28px' }}>
                  <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--lf-gold)', marginBottom: 10 }}>청구항 {i + 1}</p>
                  <textarea
                    value={claim}
                    onChange={e => {
                      const next = [...editedClaims]
                      next[i] = e.target.value
                      setEditedClaims(next)
                    }}
                    rows={6}
                    style={{
                      width: '100%', boxSizing: 'border-box',
                      fontSize: 13, fontWeight: 300, color: 'var(--lf-body)', lineHeight: 2,
                      fontFamily: 'var(--lf-sans)', background: 'var(--lf-bg2)',
                      border: '1px solid var(--lf-border)', borderBottom: '2px solid var(--lf-gold)',
                      padding: '12px 14px', resize: 'vertical', outline: 'none',
                    }}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 1, border: '1px solid var(--lf-border)', background: 'var(--lf-border)' }}>
              {claims.map((claim, i) => (
                <div key={i} style={{ background: 'var(--lf-bg)', padding: '24px 28px' }}>
                  <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--lf-gold)', marginBottom: 10 }}>청구항 {i + 1}</p>
                  <p style={{ fontSize: 13, fontWeight: 300, color: 'var(--lf-body)', lineHeight: 2, whiteSpace: 'pre-wrap' }}>{claim}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'spec' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <RegenButton agentKey="specification" label="명세서" state={state} onStateUpdate={onStateUpdate} />
          <div className="card">
            {specification ? (
              <pre style={{ fontSize: 12, fontWeight: 300, color: 'var(--lf-body)', lineHeight: 2, whiteSpace: 'pre-wrap', fontFamily: 'var(--lf-sans)' }}>{specification}</pre>
            ) : (
              <p style={{ color: 'var(--lf-muted)', fontSize: 13 }}>명세서가 아직 생성되지 않았습니다.</p>
            )}
          </div>
        </div>
      )}

      {tab === 'priorart' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <RegenButton agentKey="prior_art" label="선행기술" state={state} onStateUpdate={onStateUpdate} />
          <div className="card">
            {priorArt ? (
              <pre style={{ fontSize: 12, fontWeight: 300, color: 'var(--lf-body)', lineHeight: 2, whiteSpace: 'pre-wrap', fontFamily: 'var(--lf-sans)' }}>{priorArt}</pre>
            ) : (
              <p style={{ color: 'var(--lf-muted)', fontSize: 13 }}>선행기술 분석이 아직 완료되지 않았습니다.</p>
            )}
          </div>
        </div>
      )}

      {tab === 'raw' && (
        <div className="card">
          <pre style={{ fontSize: 11, color: 'var(--lf-mid)', overflow: 'auto', maxHeight: '60vh', fontFamily: 'Courier New, monospace', lineHeight: 1.6 }}>
            {JSON.stringify(state, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function RegenButton({ agentKey, label, state, onStateUpdate }: {
  agentKey: string; label: string
  state: Record<string, unknown>
  onStateUpdate: (s: Record<string, unknown>) => void
}) {
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState('')

  async function run() {
    setIsRunning(true); setError('')
    try {
      const result = await pipelineApi.runAgent(agentKey, state)
      onStateUpdate(result.state)
    } catch (err) {
      setError(err instanceof Error ? err.message : '재생성에 실패했습니다.')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button onClick={run} disabled={isRunning} className="btn-fill" style={{ fontSize: 10, padding: '8px 16px', opacity: isRunning ? .6 : 1 }}>
        {isRunning ? `⟳ 생성 중...` : `${label} 재생성`}
      </button>
      {error && <span style={{ fontSize: 11, color: '#ef4444' }}>{error}</span>}
    </div>
  )
}
