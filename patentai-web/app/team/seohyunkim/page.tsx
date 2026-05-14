import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export default function SeohyunkimProfile() {
  const skills = ['Next.js', 'React', 'TypeScript', 'Streamlit', 'Python', 'SVG 렌더링', 'UI/UX']
  const works = [
    { title: 'PatentAI 홈페이지', desc: 'Next.js 기반 메인 웹사이트 구현 (홈/서비스/구성원/소식)' },
    { title: '도면 에이전트', desc: '특허청 실무 수준 SVG 도면 자동 생성 에이전트' },
    { title: '발명의 설명 에이전트', desc: '특허 명세서 발명의 설명 섹션 자동 생성' },
    { title: 'Streamlit UI', desc: 'patentai_ui.py 메인 화면 및 페이지 구성' },
  ]

  return (
    <div className="site">
      <Nav />

      <div className="hero">
        <div className="tag">TEAM MEMBER</div>
        <h1>김서현</h1>
        <p>Frontend / PatentAI UI · Drawing Agent</p>
      </div>

      <div className="section">
        <Link href="/team" style={{ color: '#C9A84C', fontSize: '0.85rem', textDecoration: 'none', display: 'inline-block', marginBottom: '2rem' }}>
          ← 구성원 목록으로
        </Link>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '3rem', alignItems: 'start' }}>

          {/* 왼쪽: 프로필 카드 */}
          <div style={{ background: 'white', border: '1px solid #E8E4DC', padding: '2.5rem', boxShadow: '0 12px 30px rgba(0,0,0,0.06)' }}>
            <div style={{
              width: 100, height: 100, borderRadius: '50%',
              background: 'linear-gradient(135deg,#1A1A2E,#C9A84C)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'white', fontSize: '2rem',
              fontFamily: "'Noto Serif KR', serif",
              marginBottom: '1.5rem',
            }}>02</div>

            <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.4rem', color: '#1A1A2E' }}>김서현</div>
            <div style={{ color: '#C9A84C', fontSize: '0.88rem', fontWeight: 600, marginBottom: '1.2rem' }}>
              Frontend / PatentAI UI
            </div>

            <div style={{ borderTop: '1px solid #E8E4DC', paddingTop: '1.2rem' }}>
              <div style={{ fontSize: '0.78rem', color: '#999', marginBottom: '0.5rem', fontWeight: 600, letterSpacing: '0.1em' }}>GITHUB</div>
              <a href="https://github.com/bizseohyunkim" target="_blank" rel="noopener noreferrer"
                style={{ color: '#C9A84C', fontSize: '0.88rem', textDecoration: 'none' }}>
                @bizseohyunkim
              </a>
            </div>

            <div style={{ borderTop: '1px solid #E8E4DC', paddingTop: '1.2rem', marginTop: '1rem' }}>
              <div style={{ fontSize: '0.78rem', color: '#999', marginBottom: '0.8rem', fontWeight: 600, letterSpacing: '0.1em' }}>SKILLS</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {skills.map(s => (
                  <span key={s} style={{
                    background: '#F5F4F1', border: '1px solid #E8E4DC',
                    padding: '3px 10px', fontSize: '0.78rem', color: '#444',
                  }}>{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* 오른쪽: 담당 업무 */}
          <div>
            <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: '1.6rem', fontWeight: 300, color: '#1A1A2E', marginBottom: '0.5rem' }}>
              담당 업무
            </div>
            <div style={{ width: 40, height: 2, background: '#C9A84C', marginBottom: '1.8rem' }} />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
              {works.map((w, i) => (
                <div key={i} style={{ background: 'white', border: '1px solid #E8E4DC', padding: '1.5rem', boxShadow: '0 4px 12px rgba(0,0,0,0.04)' }}>
                  <div style={{ color: '#C9A84C', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                    0{i + 1}
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#1A1A2E', marginBottom: '0.4rem' }}>{w.title}</div>
                  <div style={{ color: '#666', fontSize: '0.9rem', lineHeight: 1.7 }}>{w.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
