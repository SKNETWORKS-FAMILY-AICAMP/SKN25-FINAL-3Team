import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const AGENTS = [
  { num: '01', name: '발명 분석', en: 'Invention Parser', desc: '발명 내용을 구조화하고 핵심 기술 요소를 파악합니다.' },
  { num: '02', name: '선행기술 조사', en: 'Prior Art Search', desc: '특허 데이터베이스를 검색하여 관련 선행기술을 분석합니다.' },
  { num: '03', name: 'AI 요약', en: 'Summary Agent', desc: '발명의 기술적 특징을 명확하고 간결하게 요약합니다.' },
  { num: '04', name: '청구항 작성', en: 'Claim Drafting', desc: '특허청 기준에 맞는 독립항·종속항 청구범위를 생성합니다.' },
  { num: '05', name: '도면 생성', en: 'Drawing Agent', desc: '블록도·흐름도 SVG를 자동으로 생성합니다.' },
  { num: '06', name: '명세서 작성', en: 'Specification Agent', desc: '출원 가능 수준의 완성된 특허 명세서를 작성합니다.' },
  { num: '07', name: '품질 검토', en: 'Quality Critic', desc: '최종 문서의 완성도와 법적 요건 충족 여부를 검토합니다.' },
]

const FEATURES = [
  { no: '01', name: 'AI 자동 생성', desc: '발명 내용을 입력하면 청구항·도면·명세서까지 자동으로 완성됩니다.' },
  { no: '02', name: '선행기술 분석', desc: '멀티에이전트 파이프라인이 선행기술을 검색하고 차별성을 분석합니다.' },
  { no: '03', name: '빠른 문서화', desc: '반복 작업 시간을 획기적으로 단축합니다. 변리사 협업도 간편합니다.' },
]

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div style={{ paddingTop: 70, background: 'var(--lf-bg)', color: 'var(--lf-navy)' }}>

      {/* Top credential bar */}
      <div style={{ background: 'var(--lf-navy)', padding: '8px 0' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 64px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
          {['등록 변리사 자문 시스템', 'AI 기반 특허 명세서 자동 작성', '선행기술조사 · 청구항 생성 · 명세서 작성', '출원 문서 자동화 플랫폼'].map((item, i) => (
            <span key={i} style={{ fontSize: 9, fontWeight: 500, letterSpacing: '1.3px', textTransform: 'uppercase', color: 'rgba(255,255,255,.4)', display: 'flex', alignItems: 'center', gap: 20 }}>
              {i > 0 && <span style={{ color: 'rgba(255,255,255,.12)' }}>|</span>}
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* Hero */}
      <section id="intro" style={{
        position: 'relative', minHeight: '100vh',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden', background: 'var(--lf-bg)',
      }}>
        {/* Dot grid overlay */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          backgroundImage: 'radial-gradient(circle, rgba(154,120,64,.11) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />
        {/* Vertical lines */}
        <div style={{ position: 'absolute', inset: 0, display: 'flex', justifyContent: 'space-evenly', pointerEvents: 'none' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} style={{ width: 1, background: 'linear-gradient(180deg, transparent 0%, rgba(154,120,64,.05) 30%, rgba(154,120,64,.05) 70%, transparent 100%)' }} />
          ))}
        </div>
        {/* Watermark */}
        <div style={{
          position: 'absolute', right: '-1vw', bottom: '-6vh',
          fontFamily: 'var(--lf-serif)', fontSize: 'clamp(180px,22vw,340px)',
          fontWeight: 300, fontStyle: 'italic', color: 'rgba(154,120,64,.04)',
          lineHeight: 1, pointerEvents: 'none', userSelect: 'none', letterSpacing: -4,
        }}>VII</div>

        {/* Content */}
        <div style={{ position: 'relative', zIndex: 5, textAlign: 'center', maxWidth: 760, padding: '0 40px' }}>
          <p style={{
            display: 'inline-flex', alignItems: 'center', gap: 20,
            fontSize: 18, fontWeight: 500, letterSpacing: '4.5px', textTransform: 'uppercase',
            color: 'var(--lf-gold)', opacity: .6, marginBottom: 44,
          }}>Patent Intelligence · AI 특허 자동화 플랫폼</p>

          <h1 style={{
            fontFamily: 'var(--lf-serif)', fontSize: 'clamp(42px,6vw,84px)',
            fontWeight: 300, lineHeight: 1.1, letterSpacing: -2, color: 'var(--lf-navy)', marginBottom: 32,
          }}>
            Protect your patent<br /><em style={{ fontStyle: 'italic', color: 'var(--lf-gold)' }}>and intellectual property</em><br />with PYPI
          </h1>

          <div style={{ width: 40, height: 1, background: 'linear-gradient(90deg, transparent, var(--lf-gold), transparent)', margin: '0 auto 28px' }} />

          <p style={{ fontSize: 16, fontWeight: 300, lineHeight: 2, color: 'var(--lf-mid)', letterSpacing: .3, marginBottom: 44, maxWidth: 560, margin: '0 auto 44px' }}>
            7개 전문 AI 에이전트가 특허청 제출 가능한 완성 명세서를 체계적으로 완성합니다
          </p>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, flexWrap: 'wrap' }}>
            {user ? (
              <Link to="/dashboard" className="btn-fill">대시보드로 이동 →</Link>
            ) : (
              <>
                <Link to="/signup" className="btn-fill">지금 시작하기 →</Link>
                <a href="#pipeline" className="btn-line">AI 에이전트 소개</a>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Credential stats bar */}
      <div style={{ background: 'var(--lf-bg2)', borderTop: '1px solid var(--lf-border)', borderBottom: '1px solid var(--lf-border)' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 64px', height: 88, display: 'flex', alignItems: 'center' }}>
          {[
            { n: '7', label: '전문 AI 에이전트' },
            { n: '4', label: '지원 언어' },
            { n: '100%', label: 'AI 자동 생성' },
          ].map((item, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, ...(i > 0 ? { borderLeft: '1px solid var(--lf-border)' } : {}) }}>
              <span style={{ fontFamily: 'var(--lf-serif)', fontSize: 32, fontWeight: 300, color: 'var(--lf-gold)', lineHeight: 1, letterSpacing: -1 }}>{item.n}</span>
              <span style={{ fontSize: 19, fontWeight: 500, letterSpacing: '2.5px', textTransform: 'uppercase', color: 'var(--lf-muted)' }}>{item.label}</span>
            </div>
          ))}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, borderLeft: '1px solid var(--lf-border)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--lf-gold)', opacity: .7 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
            <span style={{ fontFamily: 'var(--lf-serif)', fontSize: 13, fontWeight: 300, color: 'var(--lf-body)', textAlign: 'center' }}>변리사 자문 완료</span>
          </div>
        </div>
      </div>

      {/* AI Pipeline section */}
      <section id="pipeline" style={{ padding: '120px 0', background: 'var(--lf-bg2)', borderBottom: '1px solid var(--lf-border)' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 64px' }}>
          <div style={{ marginBottom: 80 }}>
            <span style={{ display: 'block', fontSize: 20, fontWeight: 600, letterSpacing: 4, textTransform: 'uppercase', color: 'var(--lf-gold)', opacity: .75, marginBottom: 22 }}>Patent Pipeline</span>
            <h2 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(26px,2.8vw,40px)', fontWeight: 300, color: 'var(--lf-navy)', lineHeight: 1.25, letterSpacing: -.4 }}>
              7개의 전문 AI 에이전트가<br /><em style={{ fontStyle: 'italic', color: 'var(--lf-gold)' }}>체계적으로 협력합니다</em>
            </h2>
          </div>
          <div style={{ position: 'relative', borderTop: '1px solid rgba(0,0,0,.07)' }}>
            <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 1, background: 'rgba(154,120,64,.15)' }} />
            {AGENTS.map((agent, i) => (
              <div key={i} style={{
                display: 'grid', gridTemplateColumns: '88px 1fr',
                padding: '44px 0 44px 32px', borderBottom: '1px solid rgba(0,0,0,.05)',
                transition: 'background .2s',
              }}>
                <span style={{ fontFamily: 'Courier New, monospace', fontSize: 28, color: 'var(--lf-gold)', opacity: .5, letterSpacing: 1 }}>{agent.num}</span>
                <div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 10 }}>
                    <span style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(20px,2vw,28px)', fontWeight: 400, color: 'var(--lf-navy)' }}>{agent.name}</span>
                    <span style={{ fontSize: 14, fontWeight: 500, letterSpacing: '2.5px', textTransform: 'uppercase', color: 'var(--lf-muted)' }}>{agent.en}</span>
                  </div>
                  <p style={{ fontSize: 18, fontWeight: 300, lineHeight: 2, color: 'var(--lf-mid)', maxWidth: 540 }}>{agent.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features section */}
      <section id="features" style={{ padding: '120px 0', background: 'var(--lf-bg)' }}>
        <div style={{ maxWidth: 1180, margin: '0 auto', padding: '0 64px' }}>
          <div style={{ marginBottom: 80 }}>
            <span style={{ display: 'block', fontSize: 16, fontWeight: 600, letterSpacing: 4, textTransform: 'uppercase', color: 'var(--lf-gold)', opacity: .75, marginBottom: 22 }}>Features</span>
            <h2 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(26px,2.8vw,40px)', fontWeight: 300, color: 'var(--lf-navy)', lineHeight: 1.25 }}>주요 기능</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 1, background: 'var(--lf-border)', border: '1px solid var(--lf-border)' }}>
            {FEATURES.map((f, i) => (
              <div key={i} style={{ background: 'var(--lf-bg)', padding: '52px 40px 48px', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden' }}>
                <span style={{ fontFamily: 'Courier New, monospace', fontSize: 26, fontWeight: 700, letterSpacing: 2, color: 'var(--lf-gold)', opacity: .55, marginBottom: 28, borderBottom: '1px solid rgba(154,120,64,.25)', paddingBottom: 8, display: 'inline-block' }}>{f.no}</span>
                <h3 style={{ fontFamily: 'var(--lf-serif)', fontSize: 26, fontWeight: 400, color: 'var(--lf-navy)', marginBottom: 14 }}>{f.name}</h3>
                <p style={{ fontSize: 17, fontWeight: 300, lineHeight: 2, color: 'var(--lf-mid)' }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      {!user && (
        <section style={{ padding: '120px 0', background: 'var(--lf-bg2)', borderTop: '1px solid var(--lf-border)', textAlign: 'center' }}>
          <div style={{ maxWidth: 640, margin: '0 auto', position: 'relative', padding: '56px 64px', border: '1px solid rgba(154,120,64,.2)' }}>
            <div style={{ marginBottom: 40 }}>
              <span style={{ fontFamily: 'Courier New, monospace', fontSize: 8, fontWeight: 500, letterSpacing: '2.5px', textTransform: 'uppercase', color: 'var(--lf-gold)', opacity: .55 }}>Get Started · 시작하기</span>
            </div>
            <h2 style={{ fontFamily: 'var(--lf-serif)', fontSize: 'clamp(32px,4.5vw,52px)', fontWeight: 300, color: 'var(--lf-navy)', lineHeight: 1.12, letterSpacing: -.5, marginBottom: 20 }}>
              지금 바로<br /><em style={{ fontStyle: 'italic', color: 'var(--lf-gold)' }}>시작하세요</em>
            </h2>
            <p style={{ fontSize: 13.5, fontWeight: 300, color: 'var(--lf-mid)', lineHeight: 1.9, marginBottom: 44 }}>
              무료로 특허 AI 서비스를 경험해보세요.<br />아이디어만 있으면 명세서가 완성됩니다.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, flexWrap: 'wrap' }}>
              <Link to="/signup" className="btn-fill">무료로 시작하기 →</Link>
              <Link to="/login" className="btn-line">로그인</Link>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
