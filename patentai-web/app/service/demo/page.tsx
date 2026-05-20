'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const SAMPLE_DRAWINGS = [
  { file: '/drawings/sample_block.svg', type: 'BLOCK DIAGRAM', title: '전체 시스템 구성도' },
  { file: '/drawings/sample_flow.svg',  type: 'FLOWCHART',     title: '처리 흐름도' },
]

const SAMPLE_INPUT = `딥러닝 기반 이미지 분류 시스템입니다.
사용자가 이미지를 업로드하면 CNN 모델이 자동으로 분류하여 결과를 반환합니다.
기존 수동 분류 방식의 정확도 한계(70%)를 AI로 95% 이상으로 개선합니다.
입력부, 전처리부, CNN 모델부, 저장부, 출력부로 구성됩니다.`

type Step = 'idle' | 'loading' | 'done' | 'error'

export default function DemoPage() {
  const [input, setInput] = useState('')
  const [step, setStep]   = useState<Step>('idle')
  const [claims, setClaims] = useState<{ claim_1: string; dependent_claims: string } | null>(null)
  const [error, setError]  = useState('')
  const [selectedDrawing, setSelectedDrawing] = useState<typeof SAMPLE_DRAWINGS[0] | null>(null)

  async function handleGenerate() {
    if (!input.trim()) return
    setStep('loading')
    setError('')
    setClaims(null)

    try {
      const res = await fetch('/api/claims', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consultation_note: input }),
      })
      const data = await res.json()

      if (!res.ok || data.error) {
        setError(data.error || '생성 중 오류가 발생했습니다.')
        setStep('error')
        return
      }

      setClaims(data)
      setStep('done')
    } catch {
      setError('백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.')
      setStep('error')
    }
  }

  function reset() {
    setStep('idle')
    setClaims(null)
    setError('')
  }

  return (
    <div className="site">
      <style>{`
        .demo-wrap { max-width: 900px; margin: 0 auto; padding: 3rem 2rem 5rem; }

        /* 스텝 인디케이터 */
        .demo-steps { display: flex; align-items: center; gap: 0; margin-bottom: 3rem; }
        .demo-step { display: flex; align-items: center; gap: .6rem; font-size: .72rem; font-weight: 700; letter-spacing: .12em; color: #bbb; }
        .demo-step.active { color: #C9A84C; }
        .demo-step.done   { color: #27ae60; }
        .demo-step-num { width: 26px; height: 26px; border: 1px solid currentColor; display: flex; align-items: center; justify-content: center; font-family: 'Noto Serif KR', serif; font-size: .75rem; flex-shrink: 0; }
        .demo-step-sep { width: 3rem; height: 1px; background: #E0DDD8; margin: 0 .4rem; }

        /* 입력 영역 */
        .demo-section { margin-bottom: 2.5rem; }
        .demo-label { font-size: .68rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; margin-bottom: .8rem; }
        .demo-textarea {
          width: 100%; min-height: 160px; padding: 1.2rem;
          border: 1px solid #E0DDD8; font-family: inherit; font-size: .88rem;
          color: #222; line-height: 1.8; resize: vertical;
          transition: border-color .15s; background: white;
          box-sizing: border-box;
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

        /* 로딩 */
        .demo-loading { display: flex; align-items: center; gap: 1rem; padding: 2rem; border: 1px solid #E0DDD8; background: #FAFAF8; }
        .demo-spinner { width: 24px; height: 24px; border: 2px solid #E0DDD8; border-top-color: #C9A84C; border-radius: 50%; animation: spin .8s linear infinite; flex-shrink: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .demo-loading-text { font-size: .88rem; color: #555; }
        .demo-loading-sub  { font-size: .76rem; color: #999; margin-top: .2rem; }

        /* 결과 */
        .demo-result { border: 1px solid #E0DDD8; }
        .demo-result-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E0DDD8; background: #FAFAF8; display: flex; align-items: center; justify-content: space-between; }
        .demo-result-tag { font-size: .65rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; }
        .demo-result-body { padding: 1.4rem; }
        .demo-claim-label { font-size: .65rem; font-weight: 700; letter-spacing: .15em; color: #888; margin-bottom: .5rem; margin-top: 1rem; }
        .demo-claim-label:first-child { margin-top: 0; }
        .demo-claim-text { font-size: .86rem; color: #222; line-height: 1.9; white-space: pre-wrap; word-break: keep-all; }

        /* 도면 */
        .demo-drawings { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #E0DDD8; margin-top: 1.5rem; }
        .demo-drawing-card { background: white; cursor: pointer; transition: background .15s; }
        .demo-drawing-card:hover { background: #FAFAF8; }
        .demo-drawing-img { width: 100%; aspect-ratio: 4/3; object-fit: contain; padding: .5rem; background: #FEFEFE; border-bottom: 1px solid #F0EDE8; display: block; }
        .demo-drawing-meta { padding: .8rem 1rem; font-size: .76rem; }
        .demo-drawing-type { color: #C9A84C; font-weight: 700; letter-spacing: .12em; margin-bottom: .2rem; font-size: .65rem; }
        .demo-drawing-title { color: #0A0A16; font-weight: 700; }

        /* 에러 */
        .demo-error { padding: 1.2rem 1.4rem; border: 1px solid rgba(231,76,60,.25); background: rgba(231,76,60,.04); }
        .demo-error-title { font-size: .8rem; font-weight: 700; color: #e74c3c; margin-bottom: .4rem; }
        .demo-error-msg { font-size: .82rem; color: #555; line-height: 1.7; }

        /* 모달 */
        .modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.8); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 2rem; }
        .modal { background: white; max-width: 900px; width: 100%; max-height: 88vh; display: flex; flex-direction: column; }
        .modal-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E8E4DC; display: flex; align-items: center; justify-content: space-between; }
        .modal-close { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: #999; line-height: 1; padding: 0; }
        .modal-close:hover { color: #C9A84C; }
        .modal-body { flex: 1; overflow: auto; padding: 1rem; }
        .modal-body img { width: 100%; height: auto; }

        @media (max-width: 600px) {
          .demo-steps { flex-wrap: wrap; gap: .5rem; }
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
        <div className="demo-steps">
          {[
            { n: '01', label: '발명 내용 입력', s: 'idle' },
            { n: '02', label: '청구항 생성', s: 'loading' },
            { n: '03', label: '도면 확인', s: 'done' },
          ].map((s, i) => {
            const cls =
              step === 'done'    ? 'done'   :
              step === 'loading' && i <= 1 ? 'active' :
              step === 'idle'    && i === 0 ? 'active' : ''
            return (
              <div key={s.n} style={{ display: 'flex', alignItems: 'center' }}>
                <div className={`demo-step ${cls}`}>
                  <div className="demo-step-num">{s.n}</div>
                  <span>{s.label}</span>
                </div>
                {i < 2 && <div className="demo-step-sep" />}
              </div>
            )
          })}
        </div>

        {/* 입력 */}
        <div className="demo-section">
          <div className="demo-label">발명 내용 (자유롭게 설명)</div>
          <textarea
            className="demo-textarea"
            placeholder="발명의 목적, 구성요소, 해결하려는 문제, 기대 효과를 자유롭게 입력하세요."
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={step === 'loading'}
          />
          <div className="demo-btn-row">
            <button
              className="demo-btn"
              onClick={handleGenerate}
              disabled={step === 'loading' || !input.trim()}
            >
              {step === 'loading' ? '생성 중...' : '청구항 + 도면 생성 →'}
            </button>
            <button
              className="demo-btn outline"
              onClick={() => setInput(SAMPLE_INPUT)}
              disabled={step === 'loading'}
            >
              샘플 입력
            </button>
            {step !== 'idle' && (
              <button className="demo-btn outline" onClick={reset}>
                초기화
              </button>
            )}
          </div>
        </div>

        {/* 로딩 */}
        {step === 'loading' && (
          <div className="demo-loading">
            <div className="demo-spinner" />
            <div>
              <div className="demo-loading-text">AI가 청구항을 생성하고 있습니다...</div>
              <div className="demo-loading-sub">EXAONE 파인튜닝 모델 + GPT-4o-mini 처리 중 (30초~2분 소요)</div>
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
        {step === 'done' && claims && (
          <>
            {/* 청구항 결과 */}
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
            <div style={{ marginTop: '2rem' }}>
              <div className="demo-label">생성된 특허 도면</div>
              <div className="demo-drawings">
                {SAMPLE_DRAWINGS.map((d, i) => (
                  <div key={i} className="demo-drawing-card" onClick={() => setSelectedDrawing(d)}>
                    <img className="demo-drawing-img" src={d.file} alt={d.title} />
                    <div className="demo-drawing-meta">
                      <div className="demo-drawing-type">{d.type}</div>
                      <div className="demo-drawing-title">{d.title}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* CTA */}
            <div style={{ marginTop: '2.5rem', display: 'flex', gap: '.8rem', flexWrap: 'wrap' }}>
              <Link href="/gallery" style={{ display: 'inline-block', padding: '.8rem 2rem', border: '1px solid #111128', background: '#111128', color: '#C9A84C', fontSize: '.82rem', fontWeight: 700, letterSpacing: '.08em', textDecoration: 'none' }}>
                도면 갤러리 보기 →
              </Link>
              <button className="demo-btn outline" onClick={reset}>
                다시 해보기
              </button>
            </div>
          </>
        )}
      </div>

      {/* 도면 모달 */}
      {selectedDrawing && (
        <div className="modal-bg" onClick={() => setSelectedDrawing(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-hd">
              <div>
                <div style={{ fontSize: '.65rem', fontWeight: 700, letterSpacing: '.15em', color: '#C9A84C', marginBottom: '3px' }}>{selectedDrawing.type}</div>
                <div style={{ fontWeight: 700, color: '#0A0A16' }}>{selectedDrawing.title}</div>
              </div>
              <button className="modal-close" onClick={() => setSelectedDrawing(null)}>×</button>
            </div>
            <div className="modal-body">
              <img src={selectedDrawing.file} alt={selectedDrawing.title} />
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}
