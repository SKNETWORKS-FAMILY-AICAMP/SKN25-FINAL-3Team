import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export interface ServiceDetailData {
  num: string
  tag: string
  title: string
  summary: string
  description: string
  steps: { num: string; title: string; desc: string }[]
  output: string[]
  related: { href: string; label: string }[]
}

export default function ServiceDetail({ d }: { d: ServiceDetailData }) {
  return (
    <div className="site">
      <style>{`
        .sd-hero { background: #111128; padding: 5rem 5.5rem 4rem; border-bottom: 2px solid #C9A84C; }
        .sd-tag { color: #C9A84C; font-size: .7rem; font-weight: 700; letter-spacing: .25em; margin-bottom: .8rem; }
        .sd-num { font-family: 'Noto Serif KR',serif; font-size: 4rem; font-weight: 300; color: rgba(201,168,76,.15); line-height: 1; margin-bottom: -.5rem; }
        .sd-title { font-family: 'Noto Serif KR',serif; font-size: 2.4rem; font-weight: 300; color: #F0EDE6; margin-bottom: 1rem; }
        .sd-summary { color: #9999B8; font-size: 1rem; line-height: 1.8; max-width: 680px; }

        .sd-body { display: grid; grid-template-columns: 1fr 1fr; gap: 3rem; padding: 4rem 5.5rem; }
        .sd-desc-title { font-family: 'Noto Serif KR',serif; font-size: 1.3rem; font-weight: 300; color: #111128; margin-bottom: .5rem; }
        .sd-line { width: 36px; height: 2px; background: #C9A84C; margin-bottom: 1.5rem; }
        .sd-desc { font-size: .92rem; line-height: 2; color: #444; word-break: keep-all; }

        .sd-steps { display: flex; flex-direction: column; gap: .6rem; }
        .sd-step { display: flex; align-items: flex-start; gap: 1rem; background: white; border: 1px solid #E8E4DC; padding: 1.2rem 1.4rem; }
        .sd-step:hover { border-color: rgba(201,168,76,.4); }
        .sd-step-num { font-family: 'Noto Serif KR',serif; color: #C9A84C; font-size: 1.1rem; font-weight: 300; flex-shrink: 0; width: 28px; }
        .sd-step-title { font-weight: 700; font-size: .9rem; color: #111128; margin-bottom: .25rem; }
        .sd-step-desc { font-size: .82rem; color: #666; line-height: 1.65; }

        .sd-output { background: #111128; padding: 3rem 5.5rem; }
        .sd-output-title { color: #C9A84C; font-size: .7rem; font-weight: 700; letter-spacing: .2em; margin-bottom: 1.2rem; }
        .sd-output-list { display: flex; flex-wrap: wrap; gap: .6rem; }
        .sd-output-item { border: 1px solid rgba(201,168,76,.3); color: #C8C8D8; font-size: .82rem; padding: .45rem 1rem; }

        .sd-related { padding: 3rem 5.5rem; background: #F5F4F1; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
        .sd-related-label { font-size: .72rem; font-weight: 700; letter-spacing: .15em; color: #C9A84C; margin-bottom: .8rem; }
        .sd-related-links { display: flex; gap: .6rem; flex-wrap: wrap; }
        .sd-related-link { border: 1px solid #E8E4DC; color: #444; font-size: .82rem; padding: .45rem 1rem; text-decoration: none; transition: .15s; background: white; }
        .sd-related-link:hover { border-color: #C9A84C; color: #C9A84C; }
        .sd-cta { display: inline-block; padding: .9rem 2.5rem; border: 1px solid #C9A84C; color: #C9A84C; text-decoration: none; font-size: .84rem; font-weight: 700; letter-spacing: .08em; transition: .2s; flex-shrink: 0; }
        .sd-cta:hover { background: #C9A84C; color: #111128; }

        @media (max-width:900px) {
          .sd-hero, .sd-body, .sd-output, .sd-related { padding: 3rem 1.5rem; }
          .sd-body { grid-template-columns: 1fr; }
        }
      `}</style>

      <Nav />

      <div className="sd-hero">
        <Link href="/service" style={{ color: '#C9A84C', fontSize: '.82rem', textDecoration: 'none', display: 'inline-block', marginBottom: '2rem' }}>← 서비스 전체 보기</Link>
        <div className="sd-tag">{d.tag}</div>
        <div className="sd-num">{d.num}</div>
        <div className="sd-title">{d.title}</div>
        <div className="sd-summary">{d.summary}</div>
      </div>

      <div className="sd-body">
        <div>
          <div className="sd-desc-title">서비스 소개</div>
          <div className="sd-line" />
          <div className="sd-desc">{d.description}</div>
        </div>
        <div>
          <div className="sd-desc-title">처리 단계</div>
          <div className="sd-line" />
          <div className="sd-steps">
            {d.steps.map(s => (
              <div className="sd-step" key={s.num}>
                <div className="sd-step-num">{s.num}</div>
                <div>
                  <div className="sd-step-title">{s.title}</div>
                  <div className="sd-step-desc">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="sd-output">
        <div className="sd-output-title">OUTPUT</div>
        <div className="sd-output-list">
          {d.output.map(o => <span key={o} className="sd-output-item">{o}</span>)}
        </div>
      </div>

      <div className="sd-related">
        <div>
          <div className="sd-related-label">RELATED SERVICES</div>
          <div className="sd-related-links">
            {d.related.map(r => (
              <Link key={r.href} className="sd-related-link" href={r.href}>{r.label}</Link>
            ))}
          </div>
        </div>
        <Link className="sd-cta" href="/contact">상담 신청하기 →</Link>
      </div>

      <Footer />
    </div>
  )
}
