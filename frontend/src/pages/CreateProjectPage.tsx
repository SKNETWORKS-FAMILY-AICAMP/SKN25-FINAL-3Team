import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { pipelineApi, projectStore } from '../api/pipeline'
import { api } from '../api/client'

const STEPS = 3
const DEMO = {
  title: '셀프 어텐션 기반 시퀀스 변환 신경망 시스템',
  problem: '기존 모델은 RNN 또는 CNN 계층에 의존하여 입력 위치 간 장거리 의존성을 학습하므로, 병렬화가 어렵고 먼 위치 간 관계를 효과적으로 반영하기 어려움.',
  prior_art: '1. 기존 기술의 구성: RNN/CNN 기반 시퀀스 처리\n\n2. 구성의 한계: 장거리 의존성 학습 어려움\n\n3. 발생 문제: 긴 입력에 대한 성능 저하',
  core_tech: '1. 발명 대상: 신경망 시스템\n\n2. 주요 구성: 멀티헤드 셀프 어텐션 메커니즘, 인코더-디코더 구조\n\n3. 입력값: 원본 문장 토큰 시퀀스 + 포지셔널 임베딩\n\n4. 처리 방식: 쿼리·키·값으로 어텐션 스코어 계산 후 가중 합산\n\n5. 출력값: 변환된 출력 시퀀스',
  expected_effect: '병렬 처리 가능으로 학습/추론 시간 단축, 장거리 의존성 학습 성능 향상',
}

const GUIDES: Record<string, { title: string; content: string }> = {
  title:           { title: '프로젝트 명칭 가이드', content: '발명의 핵심 기술 요소와 목적이 잘 드러나는 직관적인 명칭을 입력해 주세요.' },
  problem:         { title: '과제 가이드', content: '기존 기술이 가지고 있던 명확한 한계점, 비효율성, 또는 기술적 단점을 기재해 주세요.' },
  prior_art:       { title: '종래기술 가이드', content: '"기존 기술 구성 → 그 한계 → 발생 문제" 순서로 논리적으로 작성해주세요.' },
  core_tech:       { title: '핵심 구성 가이드', content: '발명 대상 / 주요 구성요소 / 입력값 / 처리 방식 / 출력값 순서로 상세히 기술해 주세요.' },
  expected_effect: { title: '기대 효과 가이드', content: '속도 향상, 정확도 향상, 자원 절감, 오류 감소, 자동화 등으로 구체화해주세요.' },
}

const STEP_LABELS = ['명칭', '과제 · 종래기술', '구성 · 효과']

export default function CreateProjectPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({ title: '', problem: '', prior_art: '', core_tech: '', expected_effect: '' })
  const [openGuide, setOpenGuide] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  function update(field: keyof typeof form, value: string) {
    setForm(f => ({ ...f, [field]: value }))
  }

  function fillDemo() {
    if (step === 1) update('title', DEMO.title)
    if (step === 2) { update('problem', DEMO.problem); update('prior_art', DEMO.prior_art) }
    if (step === 3) { update('core_tech', DEMO.core_tech); update('expected_effect', DEMO.expected_effect) }
  }

  // async function handleSubmit(e: FormEvent) {
  //   e.preventDefault()
  //   if (step < STEPS) { setStep(s => s + 1); return }
  //   setIsLoading(true); setError('')
  //   try {
  //     const user_input = [
  //       `[프로젝트 명칭]\n${form.title}`,
  //       `[해결하고자 하는 과제]\n${form.problem}`,
  //       `[종래 기술의 문제점]\n${form.prior_art}`,
  //       `[핵심 기술 구성]\n${form.core_tech}`,
  //       `[기대 효과]\n${form.expected_effect}`,
  //     ].join('\n\n')
  //     const result = await pipelineApi.run(user_input)
  //     projectStore.add({ run_id: result.run_id, title: form.title, created_at: new Date().toISOString(), status: 'running' })
  //     navigate(`/workstation/${result.run_id}`, { state: { runResult: result } })
  //   } catch (err) {
  //     setError(err instanceof Error ? err.message : '프로젝트 생성에 실패했습니다.')
  //   } finally {
  //     setIsLoading(false)
  //   }
  // }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (step < STEPS) { setStep(s => s + 1); return }
    setIsLoading(true); setError('')
    try {
      // 1. 텍스트를 이어붙이지 않고, 백엔드가 요구하는 이름(Key)에 맞춰 JSON으로 포장합니다.
      const payload = {
        title: form.title,
        problem_to_solve: form.problem,
        prior_art_problem: form.prior_art,
        core_tech: form.core_tech,
        expected_effect: form.expected_effect,
      }

      // 2. 파이프라인 API 대신, 방금 연결한 Django 백엔드 주소로 직접 쏩니다.
      const result = await api.post<{ project_id: number, message: string }>('/auth/workspace/create/', payload)      
      
      // 3. 백엔드가 run_id가 아니라 project_id를 주므로, 이에 맞춰서 스토어와 라우터를 수정합니다.
      projectStore.add({ 
        run_id: String(result.project_id), 
        title: form.title, 
        created_at: new Date().toISOString(), 
        status: 'running' 
      })
      
      // 4. 생성된 프로젝트의 워크스테이션 페이지로 이동
      navigate(`/workstation/${result.project_id}`, { state: { runResult: result } })
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '프로젝트 생성에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page-wrap" style={{ background: 'var(--lf-bg2)' }}>
      <div style={{ maxWidth: 760, margin: '0 auto', padding: '64px 40px' }}>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <span className="label" style={{ justifyContent: 'center', display: 'block' }}>New Patent Project</span>
          <h1 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(26px,3vw,36px)', fontWeight: 300, color: 'var(--lf-navy)', letterSpacing: -.4, margin: 0 }}>새 특허 프로젝트 시작하기</h1>
        </div>

        {/* Step indicators */}
        <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', marginBottom: 48 }}>
          <div style={{ position: 'absolute', top: 14, left: 0, right: 0, height: 1, background: 'var(--lf-border)', zIndex: 0 }} />
          <div style={{ position: 'absolute', top: 14, left: 0, height: 1, background: 'var(--lf-gold)', zIndex: 0, width: `${((step - 1) / (STEPS - 1)) * 100}%`, transition: 'width .3s var(--lf-ease)' }} />
          {[1, 2, 3].map(n => (
            <div key={n} style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, background: 'var(--lf-bg2)', padding: '0 12px' }}>
              <div style={{
                width: 28, height: 28, border: `1px solid ${n <= step ? 'var(--lf-gold)' : 'var(--lf-border)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: n < step ? 'var(--lf-gold)' : 'var(--lf-bg2)',
                fontFamily: 'Courier New, monospace', fontSize: 11, fontWeight: 700,
                color: n < step ? '#fff' : n === step ? 'var(--lf-gold)' : 'var(--lf-muted)',
                transition: 'all .3s',
              }}>
                {n < step ? '✓' : n}
              </div>
              <span style={{ fontSize: 9, fontWeight: 500, letterSpacing: '1.5px', textTransform: 'uppercase', color: n <= step ? 'var(--lf-gold)' : 'var(--lf-muted)' }}>{STEP_LABELS[n - 1]}</span>
            </div>
          ))}
        </div>

        {error && (
          <div style={{ background: 'rgba(239,68,68,.06)', border: '1px solid rgba(239,68,68,.3)', color: '#ef4444', padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            {step === 1 && (
              <div>
                <FieldHeader label="프로젝트 명칭" guideKey="title" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                <input type="text" value={form.title} onChange={e => update('title', e.target.value)} placeholder="예: 셀프 어텐션 기반 시퀀스 변환 신경망 시스템" required className="input-field" />
                <GuideBox guideKey="title" openGuide={openGuide} />
              </div>
            )}

            {step === 2 && (
              <>
                <div>
                  <FieldHeader label="1. 해결하고자 하는 과제" guideKey="problem" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                  <textarea value={form.problem} onChange={e => update('problem', e.target.value)} rows={6} placeholder="기존 기술의 어떤 문제를 해결하려 합니까?" required className="input-area" />
                  <GuideBox guideKey="problem" openGuide={openGuide} />
                </div>
                <div>
                  <FieldHeader label="2. 종래 기술의 문제점" guideKey="prior_art" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                  <textarea value={form.prior_art} onChange={e => update('prior_art', e.target.value)} rows={8} placeholder="기존 기술 구성 → 한계 → 발생 문제 순으로 작성" required className="input-area" />
                  <GuideBox guideKey="prior_art" openGuide={openGuide} />
                </div>
              </>
            )}

            {step === 3 && (
              <>
                <div>
                  <FieldHeader label="3. 핵심 기술 구성 (Solution)" guideKey="core_tech" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                  <textarea value={form.core_tech} onChange={e => update('core_tech', e.target.value)} rows={12} placeholder="발명 대상 / 주요 구성요소 / 입력값 / 처리 방식 / 출력값" required className="input-area" />
                  <GuideBox guideKey="core_tech" openGuide={openGuide} />
                </div>
                <div>
                  <FieldHeader label="4. 발명의 기대 효과" guideKey="expected_effect" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                  <textarea value={form.expected_effect} onChange={e => update('expected_effect', e.target.value)} rows={5} placeholder="속도 향상, 정확도 향상, 자원 절감 등 구체적 효과" className="input-area" />
                  <GuideBox guideKey="expected_effect" openGuide={openGuide} />
                </div>
              </>
            )}

            {/* Navigation */}
            <div style={{ display: 'flex', gap: 10, paddingTop: 8, borderTop: '1px solid var(--lf-border)' }}>
              {step > 1 && (
                <button type="button" onClick={() => setStep(s => s - 1)} className="btn-line" style={{ flex: 1 }}>← 이전</button>
              )}
              <button type="submit" disabled={isLoading} className="btn-fill" style={{ flex: 2, opacity: isLoading ? .6 : 1 }}>
                {step < STEPS ? '다음 단계로 →' : isLoading ? 'AI 분석 요청 중...' : '프로젝트 생성 및 AI 분석 시작 →'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

function FieldHeader({ label, guideKey, openGuide, setOpenGuide, fillDemo }: {
  label: string; guideKey: string; openGuide: string | null; setOpenGuide: (k: string | null) => void; fillDemo: () => void
}) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
      <span className="label" style={{ marginBottom: 0 }}>{label}</span>
      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={() => setOpenGuide(openGuide === guideKey ? null : guideKey)} style={{
          fontSize: 9, fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase',
          color: 'var(--lf-mid)', background: 'none', border: '1px solid var(--lf-border)',
          padding: '4px 10px', cursor: 'pointer', fontFamily: 'var(--lf-sans)', transition: 'color .2s',
        }}>가이드</button>
        <button type="button" onClick={fillDemo} style={{
          fontSize: 9, fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase',
          color: '#fff', background: 'var(--lf-gold)', border: '1px solid var(--lf-gold)',
          padding: '4px 10px', cursor: 'pointer', fontFamily: 'var(--lf-sans)',
        }}>예시 입력</button>
      </div>
    </div>
  )
}

function GuideBox({ guideKey, openGuide }: { guideKey: string; openGuide: string | null }) {
  if (openGuide !== guideKey) return null
  const g = GUIDES[guideKey]
  return (
    <div style={{ marginTop: 12, background: 'var(--lf-bg2)', borderLeft: '2px solid var(--lf-gold)', padding: '12px 16px' }}>
      <p style={{ fontSize: 11, fontWeight: 600, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--lf-gold)', marginBottom: 6 }}>{g.title}</p>
      <p style={{ fontSize: 13, fontWeight: 300, color: 'var(--lf-mid)', lineHeight: 1.8 }}>{g.content}</p>
    </div>
  )
}
