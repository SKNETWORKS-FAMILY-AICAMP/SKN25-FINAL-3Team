import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { pipelineApi, projectStore } from '../api/pipeline'

const STEPS = 3
const DEMO = {
  title: '셀프 어텐션 기반 시퀀스 변환 신경망 시스템',
  problem: '기존 모델은 RNN 또는 CNN 계층에 의존하여 입력 위치 간 장거리 의존성을 학습하므로, 병렬화가 어렵고 먼 위치 간 관계를 효과적으로 반영하기 어려움.',
  prior_art: '1. 기존 기술의 구성: RNN/CNN 기반 시퀀스 처리\n\n2. 구성의 한계: 장거리 의존성 학습 어려움\n\n3. 발생 문제: 긴 입력에 대한 성능 저하',
  core_tech: '1. 발명 대상: 신경망 시스템\n\n2. 주요 구성: 멀티헤드 셀프 어텐션 메커니즘, 인코더-디코더 구조\n\n3. 입력값: 원본 문장 토큰 시퀀스 + 포지셔널 임베딩\n\n4. 처리 방식: 쿼리·키·값으로 어텐션 스코어 계산 후 가중 합산\n\n5. 출력값: 변환된 출력 시퀀스',
  expected_effect: '병렬 처리 가능으로 학습/추론 시간 단축, 장거리 의존성 학습 성능 향상',
}

interface Guide {
  title: string
  content: string
  color: string
}

const GUIDES: Record<string, Guide> = {
  title: { title: '프로젝트 명칭 가이드', content: '발명의 핵심 기술 요소와 목적이 잘 드러나는 직관적인 명칭을 입력해 주세요.', color: 'sky' },
  problem: { title: '과제 가이드', content: '기존 기술이 가지고 있던 명확한 한계점, 비효율성, 또는 기술적 단점을 기재해 주세요.', color: 'sky' },
  prior_art: { title: '종래기술 가이드', content: '"기존 기술 구성 → 그 한계 → 발생 문제" 순서로 논리적으로 작성해주세요.', color: 'sky' },
  core_tech: { title: '핵심 구성 가이드', content: '발명 대상 / 주요 구성요소 / 입력값 / 처리 방식 / 출력값 순서로 상세히 기술해 주세요.', color: 'emerald' },
  expected_effect: { title: '기대 효과 가이드', content: '속도 향상, 정확도 향상, 자원 절감, 오류 감소, 자동화 등으로 구체화해주세요.', color: 'sky' },
}

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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (step < STEPS) { setStep(s => s + 1); return }

    setIsLoading(true)
    setError('')
    try {
      const user_input = [
        `[프로젝트 명칭]\n${form.title}`,
        `[해결하고자 하는 과제]\n${form.problem}`,
        `[종래 기술의 문제점]\n${form.prior_art}`,
        `[핵심 기술 구성]\n${form.core_tech}`,
        `[기대 효과]\n${form.expected_effect}`,
      ].join('\n\n')

      const result = await pipelineApi.run(user_input)

      projectStore.add({
        run_id: result.run_id,
        title: form.title,
        created_at: new Date().toISOString(),
        status: 'running',
      })

      navigate(`/workstation/${result.run_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '프로젝트 생성에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const stepDotClass = (n: number) =>
    n < step
      ? 'bg-sky-500 border-sky-500 text-[#0f172a]'
      : n === step
        ? 'bg-[#0f172a] border-sky-400 text-white'
        : 'bg-[#0f172a] border-slate-600 text-slate-500'

  return (
    <div className="pt-[70px] min-h-screen">
      <div className="max-w-3xl mx-auto px-8 py-12">
        <h1 className="text-center text-3xl font-bold mb-10 text-sky-400">
          새 특허 프로젝트 시작하기
        </h1>

        {/* Step indicators */}
        <div className="relative flex justify-between mb-12">
          <div className="absolute top-5 left-0 right-0 h-0.5 bg-slate-700 z-0" />
          {[1, 2, 3].map(n => (
            <div key={n} className="relative z-10 flex flex-col items-center bg-[#0f172a] px-2">
              <div
                className={`w-10 h-10 rounded-full border-2 flex items-center justify-center font-bold text-sm ${stepDotClass(n)}`}
              >
                {n < step ? '✓' : n}
              </div>
              <span className="text-xs text-slate-500 mt-1">
                {['명칭', '과제/종래기술', '구성/효과'][n - 1]}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-400 rounded-lg px-4 py-3 mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Step 1 */}
          {step === 1 && (
            <div className="card">
              <FieldHeader label="프로젝트 명칭" guideKey="title" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
              <input
                type="text"
                value={form.title}
                onChange={e => update('title', e.target.value)}
                placeholder="예: 셀프 어텐션 기반 시퀀스 변환 신경망 시스템"
                required
                className="input-field"
              />
              <GuideBox guideKey="title" openGuide={openGuide} />
              <button type="submit" className="btn-primary w-full mt-6">다음 단계로 →</button>
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && (
            <div className="card flex flex-col gap-6">
              <div>
                <FieldHeader label="1. 해결하고자 하는 과제" guideKey="problem" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                <textarea
                  value={form.problem}
                  onChange={e => update('problem', e.target.value)}
                  rows={6}
                  placeholder="기존 기술의 어떤 문제를 해결하려 합니까?"
                  required
                  className="input-field resize-vertical"
                />
                <GuideBox guideKey="problem" openGuide={openGuide} />
              </div>
              <div>
                <FieldHeader label="2. 종래 기술의 문제점" guideKey="prior_art" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                <textarea
                  value={form.prior_art}
                  onChange={e => update('prior_art', e.target.value)}
                  rows={8}
                  placeholder="기존 기술 구성 → 한계 → 발생 문제 순으로 작성"
                  required
                  className="input-field resize-vertical"
                />
                <GuideBox guideKey="prior_art" openGuide={openGuide} />
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(1)} className="btn-secondary flex-1">← 이전</button>
                <button type="submit" className="btn-primary flex-[2]">다음 단계로 →</button>
              </div>
            </div>
          )}

          {/* Step 3 */}
          {step === 3 && (
            <div className="card flex flex-col gap-6">
              <div>
                <FieldHeader label="3. 핵심 기술 구성 (Solution)" guideKey="core_tech" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                <textarea
                  value={form.core_tech}
                  onChange={e => update('core_tech', e.target.value)}
                  rows={12}
                  placeholder="발명 대상 / 주요 구성요소 / 입력값 / 처리 방식 / 출력값"
                  required
                  className="input-field resize-vertical"
                />
                <GuideBox guideKey="core_tech" openGuide={openGuide} />
              </div>
              <div>
                <FieldHeader label="4. 발명의 기대 효과" guideKey="expected_effect" openGuide={openGuide} setOpenGuide={setOpenGuide} fillDemo={fillDemo} />
                <textarea
                  value={form.expected_effect}
                  onChange={e => update('expected_effect', e.target.value)}
                  rows={5}
                  placeholder="속도 향상, 정확도 향상, 자원 절감 등 구체적 효과"
                  className="input-field resize-vertical"
                />
                <GuideBox guideKey="expected_effect" openGuide={openGuide} />
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep(2)} className="btn-secondary flex-1">← 이전</button>
                <button type="submit" disabled={isLoading} className="btn-primary flex-[2]">
                  {isLoading ? '⏳ AI 분석 요청 중...' : '프로젝트 생성 및 AI 분석 시작'}
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

function FieldHeader({
  label, guideKey, openGuide, setOpenGuide, fillDemo,
}: {
  label: string
  guideKey: string
  openGuide: string | null
  setOpenGuide: (k: string | null) => void
  fillDemo: () => void
}) {
  return (
    <div className="flex justify-between items-center mb-3">
      <label className="text-lg font-semibold text-slate-200">{label}</label>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setOpenGuide(openGuide === guideKey ? null : guideKey)}
          className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-lg cursor-pointer transition-colors"
        >
          📖 가이드
        </button>
        <button
          type="button"
          onClick={fillDemo}
          className="text-xs bg-sky-600 hover:bg-sky-500 text-white px-3 py-1 rounded-lg cursor-pointer transition-colors font-bold"
        >
          🪄 예시 입력
        </button>
      </div>
    </div>
  )
}

function GuideBox({ guideKey, openGuide }: { guideKey: string; openGuide: string | null }) {
  if (openGuide !== guideKey) return null
  const g = GUIDES[guideKey]
  return (
    <div className="mt-3 bg-[#0f172a] border-l-4 border-sky-500 rounded-lg p-4">
      <p className="text-sm font-bold text-sky-300 mb-1">{g.title}</p>
      <p className="text-sm text-slate-400">{g.content}</p>
    </div>
  )
}
