import FaqSection from '../components/FaqSection'
import Reveal from '../components/Reveal'

export default function FaqPage() {
  return (
    <div style={{ paddingTop: 70, background: 'var(--lf-bg)' }}>
      <section style={{ padding: '110px 0 70px', textAlign: 'center', background: 'var(--lf-bg2)' }}>
        <div className="container">
          <Reveal variant="scale">
            <span className="label">FAQ</span>
            <h1 style={{ fontSize: 'clamp(32px,4vw,48px)', color: 'var(--lf-navy)', marginBottom: 16 }}>
              자주 묻는 질문
            </h1>
            <p style={{ fontSize: 15.5, color: 'var(--lf-mid)', lineHeight: 1.9, maxWidth: 560, margin: '0 auto' }}>
              PYPI 사용 중 궁금한 점을 분야별로 모았습니다.
            </p>
          </Reveal>
        </div>
      </section>

      <FaqSection showHomeLink sidebar />
    </div>
  )
}
