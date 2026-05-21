'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const SAMPLE_INPUT = `딥러닝 기반 이미지 분류 시스템입니다.
사용자가 이미지를 업로드하면 CNN 모델이 자동으로 분류하여 결과를 반환합니다.
기존 수동 분류 방식의 정확도 한계(70%)를 AI로 95% 이상으로 개선합니다.
입력부, 전처리부, CNN 모델부, 저장부, 출력부로 구성됩니다.`

type PipelineStep = 'idle' | 'consulting' | 'claim' | 'drawing' | 'done' | 'error'

interface ClaimResult {
  claim_1: string
  dependent_claims: string
}

interface FigureResult {
  fig_no: string | number
  title: string
  type: string
  svg_url?: string
}

interface DrawingResult {
  figures: FigureResult[]
  reference_numerals: { number: string; label: string }[]
}

const STEPS = [
  { key: 'consulting', label: '발명 분석' },
  { key: 'claim',     label: '청구항 생성' },
  { key: 'drawing',   label: '도면 생성' },
  { key: 'done',      label: '완료' },
] as const

function StepBar({ current }: { current: PipelineStep }) {
  const order: PipelineStep[] = ['consulting', 'claim', 'drawing', 'done']
  const idx = order.indexOf(current)

  return (
    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3rem' }}>
      {STEPS.map((s, i) => {
        const stepIdx = order.indexOf(s.key as PipelineStep)
        const isDone   = idx > stepIdx
        const isActive = idx === stepIdx
        const cls = isDone ? 'done' : isActive ? 'active' : ''
        return (
          <div key={s.key} style={{ display: 'flex', alignItems: 'center' }}>
            <div className={`demo-step ${cls}`}>
              <div className="demo-step-num">
                {isDone ? '✓' : String(i + 1).padStart(2, '0')}
              </div>
              <span>{s.label}</span>
            </div>
            {i < STEPS.length - 1 && <div className="demo-step-sep" />}
          </div>
        )
      })}
    </div>
  )
}

export default function DemoPage() {
  const [input, setInput]     = useState('')
  const [step, setStep]       = useState<PipelineStep>('idle')
  const [claims, setClaims]   = useState<ClaimResult | null>(null)
  const [drawings, setDrawings] = useState<DrawingResult | null>(null)
  const [error, setError]     = useState('')
  const [selectedFig, setSelectedFig] = useState<FigureResult | null>(null)

  async function handleGenerate() {
    if (!input.trim()) return
    setStep('consulting')
    setError('')
    setClaims(null)
    setDrawings(null)

    // ── Step 1: 청구항 생성 (상담 + claim 통합 endpoint) ──
    setStep('claim')
    try {
      const res = await fetch('/api/claims', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consultation_note: input }),
      })
      const data = await res.json()
      if (!res.ok || data.error) {
        setError(data.error || '청구항 생성 중 오류가 발생했습니다.')
        setStep('error')
        return
      }
      setClaims(data)
    } catch {
      setError('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.')
      setStep('error')
      return
    }

    // ── Step 2: 도면 생성 ──
    setStep('drawing')
    try {
      const res = await fetch('/api/drawings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consultation_note: input }),
      })
      const data = await res.json()
      if (!res.ok || data.error) {
        // 도면 실패는 치명적이지 않음 — 청구항은 이미 성공
        setDrawings(null)
      } else {
        setDrawings(data)
      }
    } catch {
      setDrawings(null)
    }

    setStep('done')
  }

  function reset() {
    setStep('idle')
    setClaims(null)
    setDrawings(null)
    setError('')
  }

  const isRunning = step === 'consulting' || step === 'claim' || step === 'drawing'

  return (
    <div className="site">
      <style>{`
        .demo-wrap { max-width: 900px; margin: 0 auto; padding: 3rem 2rem 5rem; }

        .demo-step { display: flex; align-items: center; gap: .6rem; font-size: .72rem; font-weight: 700; letter-spacing: .12em; color: #bbb; }
        .demo-step.active { color: #C9A84C; }
        .demo-step.done   { color: #27ae60; }
        .demo-step-num { width: 26px; height: 26px; border: 1px solid currentColor; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif KR', serif; font-size: .75rem; flex-shrink: 0; }
        .demo-step-sep { width: 3rem; height: 1px; background: #E0DDD8; margin: 0 .4rem; }

        .demo-section { margin-bottom: 2.5rem; }
        .demo-label { font-size: .68rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; margin-bottom: .8rem; }
        .demo-textarea {
          width: 100%; min-height: 160px; padding: 1.2rem;
          border: 1px solid #E0DDD8; font-family: inherit; font-size: .88rem;
          color: #222; line-height: 1.8; resize: vertical;
          transition: border-color .15s; background: white; box-sizing: border-box;
        }
        .demo-textarea:focus { outline: none; border-color: #C9A84C; }

        .demo-btn-row { display: flex; gap: .8rem; margin-top: 1rem; flex-wrap: wrap; }
        .demo-btn {
          padding: .8rem 2rem; background: #111128; border: 1px solid #111128;
          color: #C9A84C; font-size: .82rem; font-weight: 700; letter-spacing: .1em;
          cursor: pointer; transition: .15s; font-family: inherit;
        }
        .demo-btn:hover:not(:disabled) { background: #C9A84C; color: #111128; border-color: #C9A84C; }
        .demo-btn:disabled { opacity: .45; cursor: not-allowed; }
        .demo-btn.outline { background: white; color: #444; border-color: #E0DDD8; }
        .demo-btn.outline:hover { border-color: #C9A84C; color: #C9A84C; }

        .demo-progress { border: 1px solid #E0DDD8; background: #FAFAF8; padding: 1.4rem 1.6rem; margin-bottom: 1.5rem; }
        .demo-progress-row { display: flex; align-items: center; gap: 1rem; }
        .demo-spinner { width: 20px; height: 20px; border: 2px solid #E0DDD8; border-top-color: #C9A84C; border-radius: 50%; animation: spin .8s linear infinite; flex-shrink: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .demo-progress-label { font-size: .88rem; color: #333; font-weight: 600; }
        .demo-progress-sub   { font-size: .75rem; color: #999; margin-top: .2rem; }

        .demo-result { border: 1px solid #E0DDD8; margin-bottom: 1.5rem; }
        .demo-result-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E0DDD8; background: #FAFAF8; display: flex; align-items: center; justify-content: space-between; }
        .demo-result-tag { font-size: .65rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; }
        .demo-result-body { padding: 1.4rem; }
        .demo-claim-label { font-size: .65rem; font-weight: 700; letter-spacing: .15em; color: #888; margin-bottom: .5rem; margin-top: 1rem; }
        .demo-claim-label:first-child { margin-top: 0; }
        .demo-claim-text { font-size: .86rem; color: #222; line-height: 1.9; white-space: pre-wrap; word-break: keep-all; }

        .demo-drawings { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #E0DDD8; }
        .demo-drawing-card { background: white; cursor: pointer; transition: background .15s; }
        .demo-drawing-card:hover { background: #FAFAF8; }
        .demo-drawing-img { width: 100%; aspect-ratio: 4/3; object-fit: contain; padding: .5rem; background: #FEFEFE; border-bottom: 1px solid #F0EDE8; display: block; }
        .demo-drawing-meta { padding: .8rem 1rem; font-size: .76rem; }
        .demo-drawing-type  { color: #C9A84C; font-weight: 700; letter-spacing: .12em; margin-bottom: .2rem; font-size: .65rem; }
        .demo-drawing-title { color: #0A0A16; font-weight: 700; }

        .ref-table { width: 100%; border-collapse: collapse; font-size: .8rem; margin-top: 1rem; }
        .ref-table th { background: #F5F3EF; padding: .5rem .8rem; text-align: left; font-size: .65rem; letter-spacing: .1em; color: #888; border-bottom: 1px solid #E0DDD8; }
        .ref-table td { padding: .5rem .8rem; border-bottom: 1px solid #F0EDE8; color: #333; }

        .demo-error { padding: 1.2rem 1.4rem; border: 1px solid rgba(231,76,60,.25); background: rgba(231,76,60,.04); }
        .demo-error-title { font-size: .8rem; font-weight: 700; color: #e74c3c; margin-bottom: .4rem; }
        .demo-error-msg   { font-size: .82rem; color: #555; line-height: 1.7; }

        .modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.8); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 2rem; }
        .modal { background: white; max-width: 900px; width: 100%; max-height: 88vh; display: flex; flex-direction: column; }
        .modal-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E8E4DC; display: flex; align-items: center; justify-content: space-between; }
        .modal-close { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: #999; line-height: 1; padding: 0; }
        .modal-close:hover { color: #C9A84C; }
        .modal-body { flex: 1; overflow: auto; padding: 1rem; }
        .modal-body img { width: 100%; height: auto; }

        @media (max-width: 600px) {
          .demo-step-sep { display: none; }
          .demo-drawings { grid-template-columns: 1fr; }
          .demo-btn-row { flex-direction: column; }
        }
      `}</style>

      <Nav />

      <div className="hero" style={{ borderLeft: '4px solid #C9A84C' }}>
        <div className="tag">LIVE DEMO</div>
        <h1>PatentAI 라이브 데모</h1>
        <p>발명 내용을 입력하면 AI가 청구항과 도면을 자동 생성합니다.</p>
      </div>

      <div className="demo-wrap">

        {/* 스텝 표시 */}
        {step !== 'idle' && <StepBar current={step} />}

        {/* 입력 */}
        <div className="demo-section">
          <div className="demo-label">발명 내용 (자유롭게 설명)</div>
          <textarea
            className="demo-textarea"
            placeholder="발명의 목적, 구성요소, 해결하려는 문제, 기대 효과를 자유롭게 입력하세요."
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={isRunning}
          />
          <div className="demo-btn-row">
            <button
              className="demo-btn"
              onClick={handleGenerate}
              disabled={isRunning || !input.trim()}
            >
              {isRunning ? '생성 중...' : '청구항 + 도면 생성 →'}
            </button>
            <button
              className="demo-btn outline"
              onClick={() => setInput(SAMPLE_INPUT)}
              disabled={isRunning}
            >
              샘플 입력
            </button>
            {step !== 'idle' && (
              <button className="demo-btn outline" onClick={reset} disabled={isRunning}>
                초기화
              </button>
            )}
          </div>
        </div>

        {/* 진행 상태 */}
        {isRunning && (
          <div className="demo-progress">
            <div className="demo-progress-row">
              <div className="demo-spinner" />
              <div>
                <div className="demo-progress-label">
                  {step === 'consulting' && '발명 내용을 분석하고 있습니다...'}
                  {step === 'claim'      && '청구항을 생성하고 있습니다...'}
                  {step === 'drawing'    && '도면을 생성하고 있습니다...'}
                </div>
                <div className="demo-progress-sub">
                  {step === 'claim'   && 'EXAONE 파인튜닝 모델 + GPT-4o 처리 중 (30초~2분 소요)'}
                  {step === 'drawing' && 'SVG 도면 자동 생성 중 (1~3분 소요)'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 에러 */}
        {step === 'error' && (
          <div className="demo-error">
            <div className="demo-error-title">생성 실패</div>
            <div className="demo-error-msg">{error}</div>
          </div>
        )}

        {/* 결과 */}
        {(step === 'done' || (step === 'drawing' && claims)) && claims && (
          <>
            {/* 청구항 */}
            <div className="demo-result">
              <div className="demo-result-hd">
                <div className="demo-result-tag">GENERATED CLAIMS</div>
                <span style={{ fontSize: '.72rem', color: '#27ae60', fontWeight: 700 }}>✓ 생성 완료</span>
              </div>
              <div className="demo-result-body">
                <div className="demo-claim-label">독립항 (제1항)</div>
                <div className="demo-claim-text">{claims.claim_1}</div>
                {claims.dependent_claims && (
                  <>
                    <div className="demo-claim-label">종속항</div>
                    <div className="demo-claim-text">{claims.dependent_claims}</div>
                  </>
                )}
              </div>
            </div>

            {/* 도면 */}
            {step === 'done' && (
              <div className="demo-result">
                <div className="demo-result-hd">
                  <div className="demo-result-tag">GENERATED DRAWINGS</div>
                  {drawings
                    ? <span style={{ fontSize: '.72rem', color: '#27ae60', fontWeight: 700 }}>✓ {drawings.figures.length}개 도면 생성</span>
                    : <span style={{ fontSize: '.72rem', color: '#999' }}>도면 생성 불가 (백엔드 미연결)</span>
                  }
                </div>
                <div className="demo-result-body">
                  {drawings && drawings.figures.length > 0 ? (
                    <>
                      <div className="demo-drawings">
                        {drawings.figures.map((fig, i) => (
                          <div key={i} className="demo-drawing-card" onClick={() => setSelectedFig(fig)}>
                            {fig.svg_url ? (
                              <img className="demo-drawing-img" src={fig.svg_url} alt={fig.title} />
                            ) : (
                              <div className="demo-drawing-img" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#ccc', fontSize: '.8rem' }}>
                                도 {fig.fig_no}
                              </div>
                            )}
                            <div className="demo-drawing-meta">
                              <div className="demo-drawing-type">{fig.type?.toUpperCase()}</div>
                              <div className="demo-drawing-title">{fig.title || `도 ${fig.fig_no}`}</div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {drawings.reference_numerals?.length > 0 && (
                        <>
                          <div className="demo-label" style={{ marginTop: '1.5rem' }}>참조부호</div>
                          <table className="ref-table">
                            <thead>
                              <tr>
                                <th>부호</th>
                                <th>명칭</th>
                              </tr>
                            </thead>
                            <tbody>
                              {drawings.reference_numerals.map((r, i) => (
                                <tr key={i}>
                                  <td style={{ fontWeight: 700, color: '#C9A84C' }}>{r.number}</td>
                                  <td>{r.label}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </>
                      )}
                    </>
                  ) : (
                    <p style={{ color: '#999', fontSize: '.85rem' }}>
                      도면 생성 결과가 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* CTA */}
            {step === 'done' && (
              <div style={{ display: 'flex', gap: '.8rem', flexWrap: 'wrap' }}>
                <Link href="/gallery" style={{ display: 'inline-block', padding: '.8rem 2rem', border: '1px solid #111128', background: '#111128', color: '#C9A84C', fontSize: '.82rem', fontWeight: 700, letterSpacing: '.08em', textDecoration: 'none' }}>
                  도면 갤러리 보기 →
                </Link>
                <button className="demo-btn outline" onClick={reset}>다시 해보기</button>
              </div>
            )}
          </>
        )}
      </div>

      {/* 도면 모달 */}
      {selectedFig && (
        <div className="modal-bg" onClick={() => setSelectedFig(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-hd">
              <div>
                <div style={{ fontSize: '.65rem', fontWeight: 700, letterSpacing: '.15em', color: '#C9A84C', marginBottom: '3px' }}>{selectedFig.type?.toUpperCase()}</div>
                <div style={{ fontWeight: 700, color: '#0A0A16' }}>{selectedFig.title || `도 ${selectedFig.fig_no}`}</div>
              </div>
              <button className="modal-close" onClick={() => setSelectedFig(null)}>×</button>
            </div>
            <div className="modal-body">
              {selectedFig.svg_url
                ? <img src={selectedFig.svg_url} alt={selectedFig.title} />
                : <p style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>미리보기 없음</p>
              }
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}
