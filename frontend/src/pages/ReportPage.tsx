import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { pipelineApi } from '../api/pipeline'

export default function ReportPage() {
  const { runId } = useParams<{ runId: string }>()
  const [run, setRun] = useState<any>(null)
  const [state, setState] = useState<Record<string, any>>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!runId) return
    setIsLoading(true)
    pipelineApi.getRun(runId).then((r: any) => {
      setRun(r)
      setState(r.state ?? {})
    }).catch(() => {}).finally(() => setIsLoading(false))
  }, [runId])

  if (isLoading) return <div style={{ padding: 40 }}>Loading…</div>
  if (!run) return <div style={{ padding: 40 }}>리포트를 찾을 수 없습니다.</div>

  const s = state
  const claims = Array.isArray(s.claims) ? s.claims : (s.claims?.draft_claims ? s.claims.draft_claims.map((d: any) => d.text) : [])
  const specification = typeof s.specification === 'string' ? s.specification : (s.specification?.markdown_content ?? '')

  return (
    <div style={{ padding: 40, background: '#f8f9fa', minHeight: '100vh' }}>
      <div style={{ maxWidth: 800, margin: '0 auto', background: '#fff', padding: 60, borderTop: '6px solid #9a7840' }}>
        <header style={{ textAlign: 'center', borderBottom: '2px solid #111', paddingBottom: 20, marginBottom: 30 }}>
          <h1 style={{ margin: 0 }}>{run.title}</h1>
          <p style={{ color: '#9a7840' }}>{new Date(run.created_at).toLocaleDateString()}</p>
        </header>

        <Section title="I. 발명 요약 (AI 분석)">
          <Box title="해결하고자 하는 과제">{s.ext_problem}</Box>
          <Box title="핵심 해결 방법">{s.ext_solution}</Box>
          <Box title="발명의 차별성">{s.ext_differentiation}</Box>
          <Box title="기대 효과">{s.ext_effect}</Box>
        </Section>

        <Section title="II. 특허 청구범위">
          {claims && claims.length > 0 ? claims.map((c: string, i: number) => (
            <div key={i} style={{ marginBottom: 18, paddingLeft: 12, borderLeft: '2px solid #12100e' }}>
              <h4 style={{ margin: '0 0 8px 0' }}>【청구항 {i + 1}】</h4>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{c}</p>
            </div>
          )) : <p style={{ color: '#94a3b8' }}>아직 작성된 청구항이 없습니다.</p>}
        </Section>

        {s.drawings && s.drawings.length > 0 && (
          <Section title="III. 첨부 도면">
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {s.drawings.map((d: any, i: number) => (
                <div key={i} style={{ width: 220, textAlign: 'center', padding: 12, border: '1px solid #e6eef6', background: '#f8fafc' }}>
                  <img src={d.image_url} alt={d.title} style={{ maxWidth: '100%' }} />
                  <p style={{ fontSize: 12, fontWeight: 700 }}>{d.title}</p>
                </div>
              ))}
            </div>
          </Section>
        )}

        {specification && (
          <Section title="IV. 발명의 설명">
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{specification}</div>
          </Section>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: any }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 12 }}>{title}</div>
      {children}
    </div>
  )
}

function Box({ title, children }: { title: string; children: any }) {
  return (
    <div style={{ border: '1px solid #e6eef6', padding: 16, marginBottom: 12 }}>
      <h4 style={{ margin: '0 0 8px 0', color: '#9a7840' }}>{title}</h4>
      <div style={{ whiteSpace: 'pre-wrap' }}>{children ?? '입력된 데이터가 없습니다.'}</div>
    </div>
  )
}
