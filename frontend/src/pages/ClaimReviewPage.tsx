import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ClaimReviewEvent,
  ClaimReviewInput,
  ExaminerResult,
  reviewClaimsStream,
} from '../api/claimReview'
import { useAuth } from '../contexts/AuthContext'
import './ClaimReviewPage.css'

const SAMPLE_CLAIM = `청구항 1. 사용자 단말로부터 입력 데이터를 수신하는 통신부;
상기 입력 데이터를 분석하여 분류 결과를 생성하는 프로세서; 및
상기 분류 결과를 사용자 단말에 제공하는 출력부;를 포함하는 인공지능 시스템.

청구항 2. 제1항에 있어서,
상기 프로세서는 학습된 신경망 모델을 이용하여 상기 입력 데이터를 분류하는 인공지능 시스템.`

function countClaims(claimText: string) {
  if (!claimText.trim()) return 0
  const headers = claimText.match(/^\s*(?:【\s*)?청구항\s*(?:제\s*)?\d+\s*(?:항)?\s*(?:】|[.:])?/gm)
  return headers?.length || 1
}

function RejectionList({ examiner }: { examiner: ExaminerResult | null }) {
  if (!examiner || examiner.rejections.length === 0) {
    return <p style={{ color: 'var(--lf-muted)', fontSize: 11 }}>지적된 명확성 거절 사유가 없습니다.</p>
  }
  return (
    <>
      {examiner.rejections.map((rejection, index) => (
        <div className="claim-review-rejection" key={`${index}-${rejection.claims.join('-')}`}>
          <strong>대상 청구항 {rejection.claims.join(', ') || '전체'}</strong>
          <p>{rejection.reason_text}</p>
        </div>
      ))}
    </>
  )
}

export default function ClaimReviewPage() {
  const { user, isLoading: isAuthLoading } = useAuth()
  const navigate = useNavigate()
  const [claimText, setClaimText] = useState('')
  const [status, setStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [logs, setLogs] = useState<string[]>([])
  const [error, setError] = useState('')
  const [initialExam, setInitialExam] = useState<ExaminerResult | null>(null)
  const [finalExam, setFinalExam] = useState<ExaminerResult | null>(null)
  const [finalClaims, setFinalClaims] = useState<ClaimReviewInput[]>([])
  const [wasRewritten, setWasRewritten] = useState(false)

  function loadSample() {
    setClaimText(SAMPLE_CLAIM)
  }

  function resetResult() {
    setLogs([])
    setError('')
    setInitialExam(null)
    setFinalExam(null)
    setFinalClaims([])
    setWasRewritten(false)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (isAuthLoading) return
    if (!user) {
      navigate('/signup', { state: { from: '/claim-review' } })
      return
    }
    if (claimText.trim().length < 10) {
      setError('심사할 청구항 내용을 10자 이상 입력해 주세요.')
      return
    }

    resetResult()
    setStatus('running')

    try {
      await reviewClaimsStream(
        claimText.trim(),
        (streamEvent: ClaimReviewEvent) => {
          if (streamEvent.message) setLogs(current => [...current, streamEvent.message!])

          if (streamEvent.step === 'examination' && streamEvent.examiner) {
            if (streamEvent.phase === 'initial') setInitialExam(streamEvent.examiner)
            setFinalExam(streamEvent.examiner)
          }
          if (streamEvent.step === 'rewrite') setWasRewritten(true)
          if (streamEvent.step === 'done') {
            setWasRewritten(Boolean(streamEvent.was_rewritten))
            setFinalExam(streamEvent.examiner ?? null)
            setFinalClaims(streamEvent.final_claims ?? [])
            setStatus('done')
          }
          if (streamEvent.step === 'error') {
            setError(streamEvent.message || '심사 처리 중 오류가 발생했습니다.')
            setStatus('error')
          }
        },
      )
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : '심사 요청에 실패했습니다.')
      setStatus('error')
    }
  }

  return (
    <main className="claim-review-page">
      <div className="claim-review-strip">KIPO CLARITY REVIEW · ARTICLE 42(4)(2) · AI PRE-CHECK</div>

      <section className="claim-review-hero">
        <div className="claim-review-hero-inner">
          <div>
            <span className="claim-review-eyebrow">Claim Examiner <span className="claim-review-beta">Beta</span></span>
            <h1 className="claim-review-title">작성한 청구항을<br /><em>제출 전에 심사하세요.</em></h1>
            <p className="claim-review-description">
              사용자가 작성한 청구항의 명확성을 AI 심사관이 검토합니다. 불통과한 경우 거절 사유를 반영해
              보정안을 작성하고, 한 번 더 심사해 최종 결과를 보여드립니다.
            </p>
          </div>
          <div className="claim-review-flow" aria-label="심사 진행 순서">
            {[
              ['01', '청구항 붙여넣기', '작성한 청구범위를 그대로 입력합니다.'],
              ['02', 'AI 명확성 심사', '특허법 제42조 명확성 기준을 적용합니다.'],
              ['03', '자동 보정 및 재심사', '불통과 시에만 보정 에이전트가 작동합니다.'],
            ].map(([number, title, description]) => (
              <div className="claim-review-flow-step" key={number}>
                <span>{number}</span><div><strong>{title}</strong><small>{description}</small></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="claim-review-workspace">
        <form className="claim-review-panel" onSubmit={handleSubmit}>
          <div className="claim-review-panel-header">
            <h2>청구범위 붙여넣기</h2><span>번호·유형·인용항 자동 판별</span>
          </div>
          <div className="claim-review-form-body">
            <article className="claim-review-card">
              <div className="claim-review-card-head">
                <strong>YOUR CLAIMS</strong>
                <span className="claim-review-auto-badge">AUTO PARSING</span>
              </div>
              <div className="claim-review-card-body">
                <label className="claim-review-textarea-label" htmlFor="claim-text">청구항 전문</label>
                <textarea
                  id="claim-text"
                  className="claim-review-textarea claim-review-textarea--raw"
                  value={claimText}
                  maxLength={200000}
                  placeholder={'청구항을 그대로 붙여넣어 주세요.\n\n여러 항이라면 “청구항 1.”, “청구항 2.”처럼 번호를 포함하면 독립항·종속항과 인용관계를 자동으로 판별합니다.'}
                  onChange={event => setClaimText(event.target.value)}
                />
                <div className="claim-review-card-meta">
                  <span>{countClaims(claimText)}개 청구항 자동 인식</span>
                  <span>{claimText.length.toLocaleString()} / 200,000</span>
                </div>
              </div>
            </article>

            <div className="claim-review-actions">
              <div className="claim-review-actions-group">
                <button type="button" className="btn-line" onClick={loadSample} disabled={status === 'running'}>예시 불러오기</button>
                <button type="button" className="btn-line" onClick={() => setClaimText('')} disabled={status === 'running' || !claimText}>입력 지우기</button>
              </div>
              <button type="submit" className="btn-fill" disabled={status === 'running' || isAuthLoading}>{status === 'running' ? '심사 진행 중…' : 'AI 심사 시작 →'}</button>
            </div>
            {error && <div className="claim-review-error" role="alert">{error}</div>}
          </div>
          <p className="claim-review-disclaimer">본 기능은 AI 기반 사전 검토 도구이며, 심사 결과는 법률 자문이나 특허청의 공식 판단을 대체하지 않습니다.</p>
        </form>

        <aside className="claim-review-panel claim-review-result" aria-live="polite">
          <div className="claim-review-panel-header"><h2>심사 결과</h2><span>EXAMINER REPORT</span></div>

          {status === 'idle' && (
            <div className="claim-review-empty"><div><div className="claim-review-seal">審査</div><h3>심사 대기 중</h3><p>청구항을 입력하고 심사를 시작하면<br />판단 근거와 보정 결과가 여기에 표시됩니다.</p></div></div>
          )}

          {(status === 'running' || status === 'error') && (
            <div className="claim-review-progress">
              <span className="claim-review-label">Live Process</span>
              {logs.length === 0 && <div className="claim-review-log"><span className="claim-review-log-dot" /><span>심사 요청을 준비하고 있습니다.</span></div>}
              {logs.map((log, index) => <div className="claim-review-log" key={`${index}-${log}`}><span className="claim-review-log-dot" /><span>{log}</span></div>)}
            </div>
          )}

          {status === 'done' && finalExam && (
            <div className="claim-review-result-body">
              <div className="claim-review-verdict">
                <div><span className="claim-review-label">Final Decision</span><strong>{finalExam.is_approved ? '심사 통과' : '추가 보정 필요'}</strong></div>
                <span className={`claim-review-verdict-badge ${finalExam.is_approved ? 'approved' : 'rejected'}`}>{finalExam.is_approved ? 'APPROVED' : 'REVIEW'}</span>
              </div>

              <section className="claim-review-section">
                <span className="claim-review-label">최초 심사 의견</span>
                <RejectionList examiner={initialExam} />
              </section>

              {wasRewritten && (
                <section className="claim-review-section">
                  <span className="claim-review-label">AI 보정 청구범위</span>
                  {finalClaims.map(claim => (
                    <article className="claim-review-final-claim" key={claim.claim_no}>
                      <strong>청구항 {claim.claim_no} · {claim.is_dependent ? '종속항' : '독립항'} · {claim.category}</strong>
                      <p>{claim.content}</p>
                    </article>
                  ))}
                </section>
              )}

              {!finalExam.is_approved && (
                <section className="claim-review-section"><span className="claim-review-label">재심사 의견</span><RejectionList examiner={finalExam} /></section>
              )}
            </div>
          )}
        </aside>
      </section>
    </main>
  )
}
