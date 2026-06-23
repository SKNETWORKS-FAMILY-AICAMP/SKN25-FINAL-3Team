import { Fragment, FormEvent, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { FEATURES } from '../data/features'
import FaqSection from '../components/FaqSection'
import PatentSearchModal from '../components/PatentSearchModal'
import Reveal from '../components/Reveal'

const AGENTS = [
  { num: '01', name: '발명 분석', en: 'Invention Parser', desc: '발명 내용을 구조화하고 핵심 기술 요소를 파악합니다.' },
  { num: '02', name: '선행기술 조사', en: 'Prior Art Search', desc: '특허 데이터베이스를 검색하여 관련 선행기술을 분석합니다.' },
  { num: '03', name: 'AI 요약', en: 'Summary Agent', desc: '발명의 기술적 특징을 명확하고 간결하게 요약합니다.' },
  { num: '04', name: '청구항 작성', en: 'Claim Drafting', desc: '특허청 기준에 맞는 독립항·종속항 청구범위를 생성합니다.' },
  { num: '05', name: '도면 생성', en: 'Drawing Agent', desc: '블록도·흐름도 SVG를 자동으로 생성합니다.' },
  { num: '06', name: '명세서 작성', en: 'Specification Agent', desc: '출원 가능 수준의 완성된 특허 명세서를 작성합니다.' },
  { num: '07', name: '품질 검토', en: 'Quality Critic', desc: '최종 문서의 완성도와 법적 요건 충족 여부를 검토합니다.' },
]

const PAIN_POINTS = [
  { title: '전문 인력 부재', desc: '사내에 특허 전담 인력이 없으면 선행조사부터 명세서 작성까지 모든 단계를 외부에 의존해야 합니다.' },
  { title: '반복되는 수작업', desc: '선행기술조사·청구항 설계·도면·명세서 작성이 모두 별도의 수작업으로 진행되어 시간이 오래 걸립니다.' },
  { title: '심사 대응의 어려움', desc: '청구항이 명확성 요건을 충족하는지 스스로 점검하기 어렵고, 거절 시 무엇을 고쳐야 하는지 판단이 쉽지 않습니다.' },
]

const FEATURE_ICON_MAP: Record<string, keyof typeof ICONS> = {
  'patent-search': 'search',
  'prior-art': 'layers',
  'claim-drafting': 'edit',
  'examiner': 'shieldCheck',
  'drawing': 'image',
  'specification': 'fileText',
}

const HIGHLIGHTS = [
  { icon: 'bolt' as const, title: '자동 생성', desc: '발명 내용을 입력하면 청구항·도면·명세서까지 한 번에 완성됩니다.' },
  { icon: 'search' as const, title: 'AI 선행조사', desc: 'AI/비AI 기술을 자동 판별해 pgvector DB 또는 KIPRIS 중 알맞은 경로로 검색합니다.' },
  { icon: 'check' as const, title: '자동 심사·재작성', desc: '특허법 명확성 기준으로 청구항을 심사하고, 거절되면 최대 2회까지 자동으로 재작성합니다.' },
  { icon: 'doc' as const, title: '도면 자동 생성', desc: 'Graphviz 기반으로 시스템 블록도와 방법 흐름도를 그려냅니다.' },
]

const BP_CENTER = { x: 300, y: 170 }
const BP_INNER_R = 65
const BP_OUTER_R = 145
const BP_ANGLES = [0, 60, 120, 180, 240, 300]

function bpPolar(r: number, deg: number) {
  const rad = (deg * Math.PI) / 180
  return { x: BP_CENTER.x + r * Math.cos(rad), y: BP_CENTER.y + r * Math.sin(rad) }
}

const BP_INNER_NODES = BP_ANGLES.map(a => bpPolar(BP_INNER_R, a))
const BP_OUTER_NODES = BP_ANGLES.map(a => bpPolar(BP_OUTER_R, a + 30))

const BP_HUB_LINES = BP_INNER_NODES.map(n => `M${BP_CENTER.x},${BP_CENTER.y} L${n.x.toFixed(1)},${n.y.toFixed(1)}`)
const BP_RING_LINES = BP_INNER_NODES.map((n, i) => {
  const next = BP_INNER_NODES[(i + 1) % BP_INNER_NODES.length]
  return `M${n.x.toFixed(1)},${n.y.toFixed(1)} L${next.x.toFixed(1)},${next.y.toFixed(1)}`
})
const BP_SPOKE_LINES = BP_INNER_NODES.map((n, i) => {
  const o = BP_OUTER_NODES[i]
  return `M${n.x.toFixed(1)},${n.y.toFixed(1)} L${o.x.toFixed(1)},${o.y.toFixed(1)}`
})
const BP_LINES = [...BP_HUB_LINES, ...BP_RING_LINES, ...BP_SPOKE_LINES]
const BP_NODES = [
  { ...BP_CENTER, r: 12 },
  ...BP_INNER_NODES.map(n => ({ ...n, r: 7 })),
  ...BP_OUTER_NODES.map(n => ({ ...n, r: 5 })),
]

function BlueprintDiagram({ stroke = 'var(--lf-gold)' }: { stroke?: string }) {
  return (
    <svg viewBox="0 0 600 340" width="100%" style={{ display: 'block', overflow: 'visible' }}>
      <defs>
        <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </radialGradient>
      </defs>
      <g style={{ transformOrigin: '300px 170px', animation: 'spin-slow 36s linear infinite' }}>
        <g style={{ transformOrigin: '300px 170px', animation: 'breathe 5s ease-in-out infinite' }}>
          {BP_LINES.map((d, i) => (
            <Fragment key={i}>
              <path d={d} fill="none" stroke={stroke} strokeWidth="1.3"
                strokeDasharray="220" strokeDashoffset="220"
                style={{ animation: `draw-line 1.2s ${(i * 0.09).toFixed(2)}s ease-out forwards, redraw 6s ${(i * 0.09 + 1.2).toFixed(2)}s ease-in-out infinite` }}
              />
              <path d={d} fill="none" stroke="var(--lf-gold-lt)" strokeWidth="2" strokeLinecap="round"
                strokeDasharray="3 16" opacity="0.8"
                style={{ animation: `flow 2.6s ${(i * 0.05).toFixed(2)}s linear infinite` }}
              />
            </Fragment>
          ))}
          {BP_NODES.map((n, i) => (
            <g key={i}>
              <circle cx={n.x} cy={n.y} r={n.r + 11} fill="url(#nodeGlow)" />
              <circle cx={n.x} cy={n.y} r={n.r} fill={stroke}
                style={{
                  animation: `node-pulse 2.2s ${(i * 0.18).toFixed(2)}s ease-in-out infinite`,
                  transformBox: 'fill-box', transformOrigin: 'center',
                }} />
            </g>
          ))}
        </g>
      </g>
    </svg>
  )
}

const ICONS = {
  bolt: <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></>,
  check: <path d="M20 6 9 17l-5-5" />,
  doc: <><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" /></>,
  layers: <><path d="M12 2 2 7l10 5 10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></>,
  edit: <><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z" /></>,
  shieldCheck: <><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5z" /><path d="M9 12l2 2 4-4" /></>,
  image: <><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><path d="M21 15l-5-5L5 21" /></>,
  fileText: <><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" /><path d="M9 13h6M9 17h6" /></>,
  upload: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="M17 8l-5-5-5 5" /><path d="M12 3v12" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></>,
  arrowDown: <path d="M12 4v16M6 14l6 6 6-6" />,
} as const

const COMPARISON_STATS = [
  { icon: 'clock' as const, label: '작성 시간', before: ['전문가 의뢰 시', '평균 2~3주'], after: '입력 1회, 즉시 생성' },
  { icon: 'edit' as const, label: '필요 인력', before: ['변리사·전문인력', '필수 의존'], after: '전문인력 의존 최소화' },
  { icon: 'shieldCheck' as const, label: '심사 대응', before: ['거절 사유', '직접 보정'], after: '최대 2회 자동 재작성' },
  { icon: 'upload' as const, label: '작업 방식', before: ['선행조사·청구항·도면', '개별 수작업'], after: '입력 1회로 전체 완성' },
]

const PROCESS_STEPS = [
  { icon: 'upload' as const, label: '발명 입력' },
  { icon: 'layers' as const, label: '선행기술조사' },
  { icon: 'edit' as const, label: '청구항 생성' },
  { icon: 'image' as const, label: '도면 생성' },
  { icon: 'fileText' as const, label: '명세서 완성' },
]

function Icon({ name, color = 'var(--lf-gold)', size = 20 }: { name: keyof typeof ICONS, color?: string, size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  )
}

export default function HomePage() {
  const { user } = useAuth()
  const location = useLocation()
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearchOpen, setIsSearchOpen] = useState(false)

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const targetId = location.hash.replace('#', '')
      if (targetId) {
        document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      } else {
        window.scrollTo({ top: 0 })
      }
    })

    return () => cancelAnimationFrame(frame)
  }, [location.hash])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setIsSearchOpen(true)
  }

  return (
    <div style={{ background: 'var(--lf-bg)', color: 'var(--lf-navy)', paddingTop: 70 }}>

      {/* Hero — light */}
      <section id="intro" style={{ padding: '150px 0 0', textAlign: 'center', background: 'var(--lf-bg2)' }}>
        <div className="container">
          <Reveal variant="scale">
            <h1 style={{ fontSize: 'clamp(36px,4.8vw,62px)', fontWeight: 800, lineHeight: 1.3, letterSpacing: '-1.2px', color: 'var(--lf-navy)', margin: '0 0 22px' }}>
              특허 명세서·청구항·도면 작성,<br />
              <span className="text-gradient">AI 에이전트가 한 번에 완성합니다</span>
            </h1>
          </Reveal>

          <Reveal variant="scale" delay={120}>
            <p style={{ fontSize: 18, color: 'var(--lf-mid)', lineHeight: 1.95, maxWidth: 680, margin: '0 auto 36px' }}>
              발명 내용 입력 한 번으로, 선행기술조사·청구항 작성·도면 생성·명세서 작성까지 7개 전문 AI 에이전트가 자동으로 처리합니다.
            </p>
          </Reveal>

          <Reveal variant="scale" delay={220}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 56 }}>
              {user ? (
                <Link to="/dashboard" className="btn-fill">대시보드로 이동 →</Link>
              ) : (
                <>
                  <Link to="/signup" className="btn-fill">명세서 작성하기 →</Link>
                  <a href="#pipeline" className="btn-line">AI 에이전트 소개</a>
                </>
              )}
            </div>
          </Reveal>
        </div>

        {/* Patent search */}
        <div id="patent-search" style={{ scrollMarginTop: 100 }}>
          <Reveal variant="scale" delay={320} className="container" style={{ maxWidth: 640 }}>
            <h3 style={{ fontSize: 24, fontWeight: 800, color: 'var(--lf-navy)', marginBottom: 22 }}>
              원하는 특허를 검색해보세요.
            </h3>
            <form onSubmit={handleSearch} style={{ position: 'relative' }}>
              <span style={{ position: 'absolute', left: 22, top: '50%', transform: 'translateY(-50%)', display: 'flex' }}>
                <Icon name="search" color="var(--lf-muted)" />
              </span>
              <input
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="키워드로 특허를 검색해보세요 (예: 인공지능 휠체어)"
                style={{
                  width: '100%', background: 'var(--lf-bg)', border: '1px solid var(--lf-border)', borderRadius: 999,
                  padding: '16px 24px 16px 52px', fontSize: 16, color: 'var(--lf-navy)', outline: 'none', fontFamily: 'var(--lf-sans)',
                }}
              />
            </form>
          </Reveal>
        </div>

        <PatentSearchModal isOpen={isSearchOpen} query={searchQuery} onClose={() => setIsSearchOpen(false)} />
      </section>

      {/* Bold statement */}
      <section style={{ padding: '170px 0 90px', textAlign: 'center' }}>
        <div className="container">
          <Reveal variant="scale">
            <h2 style={{ fontSize: 'clamp(28px,3.2vw,44px)', color: 'var(--lf-navy)', lineHeight: 1.42 }}>
              더 빠르게, 더 정확하게.<br /><span className="text-gradient">특허 업무 자동화의 시작</span>
            </h2>
          </Reveal>

          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20,
            maxWidth: 1080, margin: '56px auto 0',
          }}>
            {COMPARISON_STATS.map((stat, i) => (
              <Reveal key={i} delay={i * 90} style={{
                background: 'var(--lf-bg2)', borderRadius: 18, padding: '34px 24px', textAlign: 'center',
              }}>
                <div style={{
                  width: 56, height: 56, borderRadius: 14, background: 'var(--lf-bg)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px',
                }}>
                  <Icon name={stat.icon} />
                </div>
                <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--lf-navy)', marginBottom: 14 }}>{stat.label}</h3>
                <p style={{ fontSize: 14.5, color: 'var(--lf-mid)', lineHeight: 1.85, marginBottom: 14 }}>
                  {stat.before[0]}<br />{stat.before[1]}
                </p>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 10 }}>
                  <Icon name="arrowDown" color="var(--lf-gold-lt)" />
                </div>
                <p className="text-gradient" style={{ fontSize: 16.5, fontWeight: 800 }}>{stat.after}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Process flow */}
      <section style={{ padding: '50px 0 160px' }}>
        <div className="container">
          <Reveal>
            <div style={{ textAlign: 'center', marginBottom: 56 }}>
              <span className="label">Process</span>
              <h2 style={{ fontSize: 'clamp(24px,2.6vw,35px)', color: 'var(--lf-navy)', marginBottom: 10 }}>PYPI 핵심 자동화 프로세스</h2>
              <p style={{ fontSize: 15.5, color: 'var(--lf-mid)' }}>발명 입력 하나로 시작되는 자동화 프로세스</p>
            </div>
          </Reveal>
          <div style={{ display: 'flex', alignItems: 'flex-start', maxWidth: 920, margin: '0 auto' }}>
            {PROCESS_STEPS.map((step, i) => (
              <Fragment key={i}>
                <Reveal delay={i * 90} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0, width: 110 }}>
                  <div style={{
                    width: 96, height: 96, borderRadius: '50%',
                    background: 'rgba(232,41,13,.08)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16,
                  }}>
                    <Icon name={step.icon} size={30} />
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--lf-navy)', textAlign: 'center' }}>{step.label}</span>
                </Reveal>
                {i < PROCESS_STEPS.length - 1 && (
                  <div style={{ flex: 1, height: 0, borderTop: '2px dotted var(--lf-muted)', marginTop: 48 }} />
                )}
              </Fragment>
            ))}
          </div>
          <Reveal>
            <p style={{ textAlign: 'center', fontSize: 15, lineHeight: 1.9, color: 'var(--lf-mid)', marginTop: 40, maxWidth: 640, marginLeft: 'auto', marginRight: 'auto' }}>
              사용자는 각 단계의 결과를 검토만 하면 됩니다.<br />
              전문가 의뢰 시 평균 2~3주 걸리던 작업을, 입력 1회로 즉시 처리합니다.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Pain points */}
      <section style={{ padding: '0 0 70px' }}>
        <div className="container">
          <Reveal>
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
              <h2 style={{ fontSize: 'clamp(26px,2.8vw,37px)', color: 'var(--lf-navy)', marginBottom: 12 }}>발명가가 겪는 출원 준비의 현실</h2>
              <p style={{ fontSize: 16, color: 'var(--lf-mid)' }}>전문지식 없이 명세서를 준비해야 하는 부담, PYPI가 줄여드립니다</p>
            </div>
          </Reveal>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
            {PAIN_POINTS.map((p, i) => (
              <Reveal key={i} delay={i * 100} className="feature-card">
                <h3 style={{ fontSize: 17.5, fontWeight: 700, color: 'var(--lf-navy)', marginBottom: 10 }}>{p.title}</h3>
                <p style={{ fontSize: 15, lineHeight: 1.95, color: 'var(--lf-mid)' }}>{p.desc}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Highlights (4 icon cards) */}
      <section style={{ padding: '80px 0 150px' }}>
        <div className="container">
          <Reveal>
            <div style={{ textAlign: 'center', marginBottom: 48 }}>
              <span className="label">서비스 소개</span>
              <h2 style={{ fontSize: 'clamp(26px,2.8vw,37px)', color: 'var(--lf-navy)' }}>
                PYPI 하나로 <span className="text-gradient">선행조사부터 명세서까지</span>
              </h2>
            </div>
          </Reveal>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: 20 }}>
            {HIGHLIGHTS.map((h, i) => (
              <Reveal key={i} delay={i * 90} style={{ background: 'var(--lf-bg2)', borderRadius: 18, padding: '30px 24px', textAlign: 'center' }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, background: 'var(--lf-bg)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px',
                }}><Icon name={h.icon} /></div>
                <h3 style={{ fontSize: 17.5, fontWeight: 700, color: 'var(--lf-navy)', marginBottom: 8 }}>{h.title}</h3>
                <p style={{ fontSize: 14.5, lineHeight: 1.85, color: 'var(--lf-mid)' }}>{h.desc}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* AI Pipeline process circles */}
      <section id="pipeline" style={{ padding: '160px 0', background: 'var(--lf-dark)' }}>
        <div className="container">
          <Reveal variant="scale">
            <div style={{ textAlign: 'center', marginBottom: 56 }}>
              <span style={{ color: 'var(--lf-gold-lt)', fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase' }}>Patent Pipeline</span>
              <h2 style={{ fontSize: 'clamp(26px,2.8vw,37px)', color: '#fff', marginTop: 10 }}>
                <span className="text-gradient-light">7개의 전문 AI 에이전트</span>가 체계적으로 협력합니다
              </h2>
            </div>
          </Reveal>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, marginBottom: 36 }}>
            {AGENTS.map((agent, i) => (
              <Reveal key={i} delay={i * 70} style={{ textAlign: 'center' }}>
                <div style={{
                  width: 84, height: 84, borderRadius: '50%', background: 'rgba(255,255,255,.06)',
                  border: '1px solid rgba(255,255,255,.15)', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', margin: '0 auto 14px', fontSize: 15, fontWeight: 700, color: 'var(--lf-gold-lt)',
                }}>{agent.num}</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', marginBottom: 4 }}>{agent.name}</div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,.65)' }}>{agent.en}</div>
              </Reveal>
            ))}
          </div>
          <Reveal>
            <p style={{ textAlign: 'center', fontSize: 15.5, lineHeight: 1.95, color: 'rgba(255,255,255,.75)', maxWidth: 680, margin: '0 auto' }}>
              발명 분석부터 선행기술조사, 청구항·도면·명세서 작성, 품질 검토까지 —<br />
              사용자는 결과를 검토만 하면 됩니다.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Detailed features (grounded in agent code) */}
      <section id="features" style={{ padding: '160px 0', background: 'var(--lf-bg2)' }}>
        <div className="container">
          <Reveal>
            <div style={{ marginBottom: 48 }}>
              <span className="label">주요 기능</span>
              <h2 style={{ fontSize: 'clamp(26px,2.8vw,37px)', color: 'var(--lf-navy)' }}>실제 코드로 동작하는 6가지 기능</h2>
            </div>
          </Reveal>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {FEATURES.map((f, i) => (
              <Reveal key={f.slug} delay={i * 60} style={{
                display: 'grid', gridTemplateColumns: '260px 1fr', gap: 32,
                background: 'var(--lf-bg)', borderRadius: 18, padding: '36px 40px',
                boxShadow: '0 10px 28px -16px rgba(33,27,23,.12)',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                  <span style={{ fontSize: 28, fontWeight: 800, color: 'var(--lf-navy)', lineHeight: 1.3 }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <Link to={`/features/${f.slug}`} style={{ fontSize: 23, fontWeight: 800, color: 'var(--lf-navy)', lineHeight: 1.3 }}>{f.name}</Link>
                </div>
                <div>
                  <p style={{ fontSize: 15.5, lineHeight: 1.95, color: 'var(--lf-mid)', marginBottom: 18 }}>{f.tagline}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                    {f.specs.slice(0, 4).map((s, j) => (
                      <span key={j} style={{
                        fontSize: 14, background: 'var(--lf-bg2)', border: '1px solid var(--lf-border)',
                        borderRadius: 8, padding: '9px 16px', color: 'var(--lf-mid)',
                      }}>
                        <span style={{ color: 'var(--lf-gold)', fontWeight: 700 }}>#{s.label}</span>: {s.value}
                      </span>
                    ))}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Before / After comparison */}
      <section style={{ padding: '130px 0' }}>
        <div className="container" style={{ maxWidth: 980 }}>
          <Reveal>
            <div style={{ marginBottom: 40, textAlign: 'center' }}>
              <span className="label">Before / After</span>
              <h2 style={{ fontSize: 'clamp(28px,3vw,41px)', color: 'var(--lf-navy)' }}>
                PYPI 도입 전과 후는 <span className="text-gradient">다릅니다</span>
              </h2>
            </div>
          </Reveal>

          <Reveal style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderRadius: 20, overflow: 'hidden', background: 'var(--lf-bg2)' }}>
            <div style={{ padding: '20px 32px', textAlign: 'center' }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--lf-muted)' }}>PYPI 도입 전</span>
            </div>
            <div style={{ padding: '20px 32px', textAlign: 'center', background: 'var(--lf-dark)' }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: '#fff' }}>PYPI 도입 시</span>
            </div>

            {[
              { label: '명세서를 자동으로 작성하는가', before: false, after: true },
              { label: '선행기술을 자동으로 분석하는가', before: false, after: true },
              { label: '근거 문헌(특허 원문)을 함께 제시하는가', before: false, after: true },
              { label: '청구항 형식·인용관계를 자동 검토하는가', before: false, after: true },
              { label: '도면을 자동으로 생성하는가', before: false, after: true },
            ].map((row, i) => (
              <Fragment key={i}>
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                  padding: '18px 32px', background: 'var(--lf-bg)',
                  borderTop: '1px solid var(--lf-bg2)',
                }}>
                  <span style={{ fontSize: 15, color: 'var(--lf-mid)' }}>{row.label}</span>
                  <span style={{ fontSize: 17, fontWeight: 700, color: 'var(--lf-muted)' }}>X</span>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
                  padding: '18px 32px', background: 'var(--lf-dark)',
                  borderTop: '1px solid rgba(255,255,255,.08)',
                }}>
                  <span style={{ fontSize: 15, color: 'rgba(255,255,255,.85)', fontWeight: 500 }}>{row.label}</span>
                  <span style={{ fontSize: 17, fontWeight: 700, color: 'var(--lf-gold-lt)' }}>O</span>
                </div>
              </Fragment>
            ))}
          </Reveal>
        </div>
      </section>

      {/* Chart comparison cards */}
      <section style={{ padding: '0 0 100px' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
          <Reveal className="stat-card">
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--lf-navy)', marginBottom: 6, textAlign: 'center' }}>출원 준비 단계</h3>
            <p style={{ fontSize: 14.5, color: 'var(--lf-mid)', textAlign: 'center', marginBottom: 28 }}>
              7단계 작업을 입력 1번으로 처리합니다
            </p>
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 28, height: 140 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 70, height: 120, background: 'var(--lf-bg3)', borderRadius: 10, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 10 }}>
                  <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--lf-mid)' }}>7단계</span>
                </div>
                <span style={{ display: 'block', fontSize: 13.5, color: 'var(--lf-muted)', marginTop: 8 }}>직접 준비</span>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ width: 70, height: 32, background: 'var(--lf-gold)', borderRadius: 10, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 6 }}>
                  <span style={{ fontSize: 15, fontWeight: 700, color: '#fff' }}>1회</span>
                </div>
                <span style={{ display: 'block', fontSize: 13.5, color: 'var(--lf-navy)', fontWeight: 600, marginTop: 8 }}>PYPI 입력</span>
              </div>
            </div>
          </Reveal>

          <Reveal delay={100} className="stat-card">
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--lf-navy)', marginBottom: 6, textAlign: 'center' }}>AI 에이전트 파이프라인</h3>
            <p style={{ fontSize: 14.5, color: 'var(--lf-mid)', textAlign: 'center', marginBottom: 24 }}>
              발명 분석부터 명세서 완성까지 순서대로 처리됩니다
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              {AGENTS.slice(0, 4).map((a, i) => (
                <div key={i} style={{
                  width: `${100 - i * 14}%`, maxWidth: 280,
                  background: i === 0 ? 'var(--lf-gold)' : 'var(--lf-bg3)',
                  borderRadius: 8, padding: '8px 0', textAlign: 'center',
                }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: i === 0 ? '#fff' : 'var(--lf-mid)' }}>{a.name}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* Stat cards */}
      <section style={{ padding: '0 0 120px' }}>
        <div className="container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
          <Reveal className="stat-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, color: 'var(--lf-mid)', marginBottom: 14 }}>전문 AI 에이전트</div>
            <div style={{ fontSize: 46, fontWeight: 800, color: 'var(--lf-gold)' }}>7개</div>
          </Reveal>
          <Reveal delay={80} className="stat-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, color: 'var(--lf-mid)', marginBottom: 14 }}>생성되는 도면 종류</div>
            <div style={{ fontSize: 46, fontWeight: 800, color: 'var(--lf-gold)' }}>2종</div>
          </Reveal>
          <Reveal delay={160} className="stat-card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 15, color: 'var(--lf-mid)', marginBottom: 14 }}>최대 청구항 보정 횟수</div>
            <div style={{ fontSize: 46, fontWeight: 800, color: 'var(--lf-navy)' }}>2회</div>
          </Reveal>
        </div>
      </section>

      {/* FAQ */}
      <FaqSection id="faq" showHeading />

      {/* Closing CTA */}
      <section style={{ padding: '130px 0 150px', textAlign: 'center' }}>
        <Reveal variant="scale" className="container" style={{
          maxWidth: 900, borderRadius: 28, padding: '80px 48px',
          background: 'var(--lf-dark)', color: '#fff',
        }}>
          <span style={{
            display: 'inline-block', fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase',
            color: '#fff', background: 'rgba(255,255,255,.12)', borderRadius: 999, padding: '7px 16px', marginBottom: 24,
          }}>Get Started</span>
          <h2 style={{ fontSize: 'clamp(30px,3.8vw,45px)', color: '#fff', lineHeight: 1.32, marginBottom: 18 }}>
            지금 바로 <span className="text-gradient-light">시작하세요</span>
          </h2>
          <p style={{ fontSize: 16.5, color: 'rgba(255,255,255,.75)', lineHeight: 1.95, marginBottom: 36 }}>
            특허 AI 서비스를 지금 경험해보세요.<br />아이디어만 있으면 명세서가 완성됩니다.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, flexWrap: 'wrap' }}>
            <Link to="/create" className="btn-fill" style={{ background: '#fff', color: 'var(--lf-navy)', borderColor: '#fff' }}>명세서 작성하기 →</Link>
            <Link to="/login" className="btn-line" style={{ background: 'transparent', color: '#fff', borderColor: 'rgba(255,255,255,.3)' }}>로그인</Link>
          </div>
        </Reveal>
      </section>
    </div>
  )
}
