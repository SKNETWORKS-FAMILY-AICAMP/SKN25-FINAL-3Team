import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { pipelineApi } from '../api/pipeline'

export default function Workstation() {
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
  if (!run) return <div style={{ padding: 40 }}>런 정보를 찾을 수 없습니다.</div>

  const invention = state.invention_input ?? {}
  const consultation = state.consultation_state ?? state ?? {}

  return (
    <div style={{ paddingTop: 40, display: 'flex', gap: 24 }}>
      <aside style={{ width: 320 }}>
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ margin: 0 }}>발명 원본 데이터</h3>
          <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
            <span style={{ background: '#f3f4f6', padding: '4px 8px', borderRadius: 6 }}>Origin Data</span>
            <a href={`/report/${run.run_id}`} target="_blank" rel="noreferrer" style={{ background: '#fef3c7', padding: '4px 8px', borderRadius: 6 }}>리포트 보기</a>
          </div>
        </div>

        <div style={{ display: 'grid', gap: 12 }}>
          <Card title="1. 해결하고자 하는 과제">{invention.problem_to_solve ?? run.user_input}</Card>
          <Card title="2. 종래 기술의 문제점">{invention.prior_art_problem}</Card>
          <Card title="3. 핵심 기술 구성">{invention.core_tech}</Card>
          <Card title="4. 기대 효과">{invention.expected_effect}</Card>
        </div>

        <div style={{ marginTop: 20 }}>
          <h4>AI Agent Analysis</h4>
          <div style={{ display: 'grid', gap: 10 }}>
            <SmallCard title="추출된 핵심 문제점">{consultation.ext_problem}</SmallCard>
            <SmallCard title="추출된 해결 방법">{consultation.ext_solution}</SmallCard>
            <SmallCard title="추출된 차별성">{consultation.ext_differentiation}</SmallCard>
            <SmallCard title="추출된 기대 효과">{consultation.ext_effect}</SmallCard>
          </div>
        </div>
      </aside>

      <main style={{ flex: 1 }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <h2 style={{ margin: 0 }}>{run.title ?? run.run_id}</h2>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn">파이프라인 상태</button>
            <button className="btn btn-gold">청구항 작성</button>
            <button className="btn">청구항 수정</button>
            <button className="btn btn-primary">도면 생성</button>
            <button className="btn btn-primary">명세서 작성</button>
          </div>
        </header>

        <div style={{ border: '1px solid #e6eef6', padding: 18, minHeight: 300 }}>          
          <div style={{ marginBottom: 12, color: '#475569' }}>{state.chat_messages ? state.chat_messages.map((m: any, i: number) => <div key={i}>{m.role}: {m.content}</div>) : '대화가 없습니다.'}</div>
        </div>
      </main>
    </div>
  )
}

function Card({ title, children }: { title: string; children: any }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e6eef6', padding: 14 }}>
      <h4 style={{ margin: '0 0 8px 0' }}>{title}</h4>
      <p style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#334155' }}>{children ?? '(입력되지 않음)'}</p>
    </div>
  )
}

function SmallCard({ title, children }: { title: string; children: any }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #eef2ff', padding: 10 }}>
      <h5 style={{ margin: '0 0 6px 0', fontSize: 12, color: '#9a7840' }}>{title}</h5>
      <p style={{ margin: 0, fontSize: 13, color: '#475569', whiteSpace: 'pre-wrap' }}>{children ?? '분석 대기 중...'}</p>
    </div>
  )
}
