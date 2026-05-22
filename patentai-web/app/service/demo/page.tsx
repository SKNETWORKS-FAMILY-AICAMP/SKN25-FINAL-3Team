'use client'

import { useRef, useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

type Step = 'idle' | 'extracting' | 'loading' | 'done' | 'error'

const TYPE_META: Record<string, { label: string; color: string }> = {
  block_diagram: { label: '블록도',          color: '#1a6fb5' },
  flowchart:     { label: '흐름도',          color: '#27ae60' },
  sequence:      { label: '시퀀스 다이어그램', color: '#8e44ad' },
  ui_screen:     { label: '화면 예시도',      color: '#e67e22' },
  circuit:       { label: '회로도',          color: '#c0392b' },
}

function typeLabel(type: string) {
  return TYPE_META[type]?.label ?? type.toUpperCase()
}
function typeColor(type: string) {
  return TYPE_META[type]?.color ?? '#C9A84C'
}

interface FigureItem {
  fig_no: string | number
  title: string
  type: string
  svg_url?: string
}

interface DrawingResult {
  figures: FigureItem[]
  reference_numerals: { number: string; label: string }[]
}

export default function DemoPage() {
  const [mode, setMode]         = useState<'text' | 'pdf'>('text')
  const [input, setInput]       = useState('')
  const [fileName, setFileName] = useState('')
  const [step, setStep]         = useState<Step>('idle')
  const [drawings, setDrawings] = useState<DrawingResult | null>(null)
  const [error, setError]       = useState('')
  const [selectedFig, setSelectedFig] = useState<FigureItem | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  async function handlePdfUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setStep('extracting')
    setError('')
    setInput('')

    try {
      const arrayBuffer = await file.arrayBuffer()
      const { getDocument, GlobalWorkerOptions } = await import('pdfjs-dist')
      GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${(await import('pdfjs-dist')).version}/build/pdf.worker.min.mjs`

      const pdf = await getDocument({ data: arrayBuffer }).promise
      const pages: string[] = []
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i)
        const content = await page.getTextContent()
        pages.push(content.items.map((item: any) => ('str' in item ? item.str : '')).join(' '))
      }
      const text = pages.join('\n').trim()
      if (!text) {
        setError('PDF에서 텍스트를 추출할 수 없습니다.')
        setStep('error')
        return
      }
      setInput(text)
      setStep('idle')
    } catch {
      setError('PDF 추출 중 오류가 발생했습니다.')
      setStep('error')
    }
  }

  async function handleGenerate() {
    if (!input.trim()) return
    setStep('loading')
    setError('')
    setDrawings(null)

    try {
      const res = await fetch('/api/drawings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consultation_note: input }),
      })
      const data = await res.json()
      if (!res.ok || data.error) {
        setError(data.error || '도면 생성 중 오류가 발생했습니다.')
        setStep('error')
        return
      }
      setDrawings(data)
      setStep('done')
    } catch {
      setError('백엔드 서버에 연결할 수 없습니다.')
      setStep('error')
    }
  }

  function reset() {
    setStep('idle')
    setDrawings(null)
    setError('')
    setInput('')
    setFileName('')
    if (fileRef.current) fileRef.current.value = ''
  }

  const isRunning = step === 'extracting' || step === 'loading'

  return (
    <div className="site">
      <style>{`
        .demo-wrap { max-width: 900px; margin: 0 auto; padding: 3rem 2rem 5rem; }

        .tab-row { display: flex; margin-bottom: 1.5rem; border: 1px solid #E0DDD8; width: fit-content; }
        .tab-btn { padding: .6rem 1.6rem; font-size: .75rem; font-weight: 700; letter-spacing: .12em; cursor: pointer; border: none; background: white; color: #999; font-family: inherit; transition: .15s; }
        .tab-btn.active { background: #111128; color: #C9A84C; }
        .tab-btn:hover:not(.active) { background: #F5F3EF; color: #555; }

        .demo-label { font-size: .68rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; margin-bottom: .8rem; }
        .demo-textarea {
          width: 100%; min-height: 160px; padding: 1.2rem;
          border: 1px solid #E0DDD8; font-family: inherit; font-size: .88rem;
          color: #222; line-height: 1.8; resize: vertical;
          transition: border-color .15s; background: white; box-sizing: border-box;
        }
        .demo-textarea:focus { outline: none; border-color: #C9A84C; }

        .upload-zone {
          border: 2px dashed #E0DDD8; padding: 3rem 2rem; text-align: center;
          cursor: pointer; transition: .15s; background: #FAFAF8;
        }
        .upload-zone:hover { border-color: #C9A84C; background: #FBF9F5; }
        .upload-zone.has-file { border-color: #27ae60; background: rgba(39,174,96,.04); }
        .upload-icon { font-size: 2rem; margin-bottom: .6rem; }
        .upload-text { font-size: .85rem; color: #555; }
        .upload-sub  { font-size: .75rem; color: #999; margin-top: .3rem; }
        .upload-filename { font-size: .85rem; color: #27ae60; font-weight: 700; margin-top: .4rem; }
        .upload-preview { margin-top: .8rem; padding: .8rem 1rem; background: #F5F3EF; font-size: .78rem; color: #666; line-height: 1.6; text-align: left; }

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

        .demo-loading { display: flex; align-items: center; gap: 1rem; padding: 2rem; border: 1px solid #E0DDD8; background: #FAFAF8; margin-top: 1.5rem; }
        .demo-spinner { width: 24px; height: 24px; border: 2px solid #E0DDD8; border-top-color: #C9A84C; border-radius: 50%; animation: spin .8s linear infinite; flex-shrink: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .demo-loading-text { font-size: .88rem; color: #555; }
        .demo-loading-sub  { font-size: .75rem; color: #999; margin-top: .2rem; }

        .demo-result { border: 1px solid #E0DDD8; margin-top: 2rem; }
        .demo-result-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E0DDD8; background: #FAFAF8; display: flex; align-items: center; justify-content: space-between; }
        .demo-result-tag { font-size: .65rem; font-weight: 700; letter-spacing: .2em; color: #C9A84C; }
        .demo-result-body { padding: 1.4rem; }

        .demo-drawings { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: #E0DDD8; }
        .demo-drawing-card { background: white; cursor: pointer; transition: background .15s; }
        .demo-drawing-card:hover { background: #FAFAF8; }
        .demo-drawing-img { width: 100%; aspect-ratio: 4/3; object-fit: contain; padding: .5rem; background: #FEFEFE; border-bottom: 1px solid #F0EDE8; display: block; }
        .demo-drawing-placeholder { width: 100%; aspect-ratio: 4/3; display: flex; align-items: center; justify-content: center; background: #F8F6F2; border-bottom: 1px solid #F0EDE8; color: #bbb; font-size: 1.5rem; font-family: 'Noto Serif KR', serif; }
        .demo-drawing-meta { padding: .8rem 1rem; font-size: .76rem; }
        .demo-drawing-type  { color: #C9A84C; font-weight: 700; letter-spacing: .12em; margin-bottom: .2rem; font-size: .65rem; }
        .demo-drawing-title { color: #0A0A16; font-weight: 700; }

        .ref-table { width: 100%; border-collapse: collapse; font-size: .8rem; margin-top: 1.5rem; }
        .ref-table th { background: #F5F3EF; padding: .5rem .8rem; text-align: left; font-size: .65rem; letter-spacing: .1em; color: #888; border-bottom: 1px solid #E0DDD8; }
        .ref-table td { padding: .5rem .8rem; border-bottom: 1px solid #F0EDE8; color: #333; }

        .demo-error { padding: 1.2rem 1.4rem; border: 1px solid rgba(231,76,60,.25); background: rgba(231,76,60,.04); margin-top: 1.5rem; }
        .demo-error-title { font-size: .8rem; font-weight: 700; color: #e74c3c; margin-bottom: .4rem; }
        .demo-error-msg { font-size: .82rem; color: #555; line-height: 1.7; }

        .modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.8); z-index: 9999; display: flex; align-items: center; justify-content: center; padding: 2rem; }
        .modal { background: white; max-width: 900px; width: 100%; max-height: 88vh; display: flex; flex-direction: column; }
        .modal-hd { padding: 1rem 1.4rem; border-bottom: 1px solid #E8E4DC; display: flex; align-items: center; justify-content: space-between; }
        .modal-close { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: #999; line-height: 1; padding: 0; }
        .modal-close:hover { color: #C9A84C; }
        .modal-body { flex: 1; overflow: auto; padding: 1rem; display: flex; align-items: center; justify-content: center; }
        .modal-body img { max-width: 100%; height: auto; }

        @media (max-width: 600px) {
          .demo-drawings { grid-template-columns: 1fr; }
          .demo-btn-row { flex-direction: column; }
        }
      `}</style>

      <Nav />

      <div className="hero" style={{ borderLeft: '4px solid #C9A84C' }}>
        <div className="tag">LIVE DEMO</div>
        <h1>특허 도면 자동 생성</h1>
        <p>발명 내용 또는 논문 PDF를 입력하면 AI가 특허 도면을 자동으로 생성합니다.</p>
      </div>

      <div className="demo-wrap">

        {/* 입력 탭 */}
        <div className="tab-row">
          <button className={`tab-btn ${mode === 'text' ? 'active' : ''}`}
            onClick={() => { setMode('text'); reset() }}>텍스트 입력</button>
          <button className={`tab-btn ${mode === 'pdf' ? 'active' : ''}`}
            onClick={() => { setMode('pdf'); reset() }}>PDF / 논문 업로드</button>
        </div>

        {/* 텍스트 입력 */}
        {mode === 'text' && (
          <>
            <div className="demo-label">발명 내용</div>
            <textarea
              className="demo-textarea"
              placeholder="발명의 목적, 구성요소, 해결하려는 문제, 기대 효과를 자유롭게 입력하세요."
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={isRunning}
            />
          </>
        )}

        {/* PDF 업로드 */}
        {mode === 'pdf' && (
          <>
            <div className="demo-label">PDF / 논문 업로드</div>
            <div
              className={`upload-zone ${fileName ? 'has-file' : ''}`}
              onClick={() => !isRunning && fileRef.current?.click()}
            >
              <div className="upload-icon">{fileName ? '✓' : '📄'}</div>
              {fileName ? (
                <>
                  <div className="upload-filename">{fileName}</div>
                  <div className="upload-sub">텍스트 추출 완료 — 클릭하여 다른 파일 선택</div>
                </>
              ) : (
                <>
                  <div className="upload-text">클릭하여 PDF 파일 선택</div>
                  <div className="upload-sub">특허 문서, 논문, 기술 보고서 (.pdf)</div>
                </>
              )}
            </div>
            <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handlePdfUpload} />
            {input && fileName && (
              <div className="upload-preview">
                <strong>추출된 텍스트 미리보기</strong><br />
                {input.slice(0, 300)}...
              </div>
            )}
          </>
        )}

        {/* 버튼 */}
        <div className="demo-btn-row">
          <button className="demo-btn" onClick={handleGenerate} disabled={isRunning || !input.trim()}>
            {step === 'loading' ? '도면 생성 중...' : '도면 생성 →'}
          </button>
          {(step !== 'idle' || input) && (
            <button className="demo-btn outline" onClick={reset} disabled={isRunning}>초기화</button>
          )}
        </div>

        {/* 로딩 */}
        {isRunning && (
          <div className="demo-loading">
            <div className="demo-spinner" />
            <div>
              <div className="demo-loading-text">
                {step === 'extracting' ? 'PDF에서 텍스트를 추출하고 있습니다...' : 'AI가 특허 도면을 생성하고 있습니다...'}
              </div>
              {step === 'loading' && (
                <div className="demo-loading-sub">발명 구조 분석 → 도면 설계 → SVG 렌더링 (1~2분 소요)</div>
              )}
            </div>
          </div>
        )}

        {/* 에러 */}
        {step === 'error' && (
          <div className="demo-error">
            <div className="demo-error-title">오류 발생</div>
            <div className="demo-error-msg">{error}</div>
          </div>
        )}

        {/* 결과 */}
        {step === 'done' && drawings && (
          <div className="demo-result">
            <div className="demo-result-hd">
              <div className="demo-result-tag">GENERATED DRAWINGS</div>
              <span style={{ fontSize: '.72rem', color: '#27ae60', fontWeight: 700 }}>
                ✓ 도면 {drawings.figures.length}개 생성 완료
              </span>
            </div>
            <div className="demo-result-body">
              <div className="demo-drawings">
                {drawings.figures.map((fig, i) => (
                  <div key={i} className="demo-drawing-card" onClick={() => setSelectedFig(fig)}>
                    {fig.svg_url
                      ? <img className="demo-drawing-img" src={fig.svg_url} alt={fig.title} />
                      : <div className="demo-drawing-placeholder">도 {fig.fig_no}</div>
                    }
                    <div className="demo-drawing-meta">
                      <div className="demo-drawing-type" style={{ color: typeColor(fig.type) }}>
                        {typeLabel(fig.type)}
                      </div>
                      <div className="demo-drawing-title">{fig.title || `도 ${fig.fig_no}`}</div>
                    </div>
                  </div>
                ))}
              </div>

              {drawings.reference_numerals?.length > 0 && (
                <>
                  <div className="demo-label" style={{ marginTop: '2rem' }}>참조부호</div>
                  <table className="ref-table">
                    <thead><tr><th>부호</th><th>명칭</th></tr></thead>
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
            </div>
          </div>
        )}
      </div>

      {/* 모달 */}
      {selectedFig && (
        <div className="modal-bg" onClick={() => setSelectedFig(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-hd">
              <div>
                <div style={{ fontSize: '.65rem', fontWeight: 700, letterSpacing: '.15em', color: typeColor(selectedFig.type), marginBottom: '3px' }}>
                  {typeLabel(selectedFig.type)}
                </div>
                <div style={{ fontWeight: 700, color: '#0A0A16' }}>{selectedFig.title || `도 ${selectedFig.fig_no}`}</div>
              </div>
              <button className="modal-close" onClick={() => setSelectedFig(null)}>×</button>
            </div>
            <div className="modal-body">
              {selectedFig.svg_url
                ? <img src={selectedFig.svg_url} alt={selectedFig.title} />
                : <p style={{ color: '#999' }}>미리보기 없음</p>
              }
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}
