import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

export interface WorkItem {
  title: string
  desc: string
}

export interface MemberData {
  num: string
  name: string
  role: string
  github: string
  skills: string[]
  works: WorkItem[]
}

export default function MemberProfile({ m }: { m: MemberData }) {
  return (
    <div className="site">
      <style>{`
        .profile-layout {
          display: grid; grid-template-columns: 1fr 2fr;
          gap: 4rem; align-items: start;
        }
        .profile-card {
          background: #111128; padding: 2.5rem;
          position: sticky; top: 2rem;
        }
        .profile-avatar {
          width: 90px; height: 90px; border-radius: 50%;
          background: linear-gradient(135deg, #1A1A2E, #C9A84C);
          display: flex; align-items: center; justify-content: center;
          color: white; font-family: 'Noto Serif KR', serif;
          font-size: 1.8rem; font-weight: 300;
          margin-bottom: 1.5rem;
          border: 2px solid rgba(201,168,76,0.4);
        }
        .profile-num {
          color: #C9A84C; font-size: 0.7rem; font-weight: 700;
          letter-spacing: 0.2em; margin-bottom: 0.4rem;
        }
        .profile-name {
          color: #F0EDE6; font-size: 1.5rem; font-weight: 700;
          margin-bottom: 0.3rem;
        }
        .profile-role {
          color: #C9A84C; font-size: 0.82rem; font-weight: 600;
          letter-spacing: 0.05em; margin-bottom: 1.5rem;
        }
        .profile-divider { height: 1px; background: rgba(201,168,76,0.2); margin-bottom: 1.2rem; }
        .profile-info-row {
          margin-bottom: 1.2rem;
        }
        .profile-info-label {
          color: #C9A84C; font-size: 0.68rem; font-weight: 700;
          letter-spacing: 0.2em; margin-bottom: 0.4rem;
        }
        .profile-info-value {
          color: #9999B8; font-size: 0.84rem; line-height: 1.6;
        }
        .profile-info-value a {
          color: #C9A84C; text-decoration: none; transition: opacity 0.15s;
        }
        .profile-info-value a:hover { opacity: 0.7; }
        .profile-skills { display: flex; flex-wrap: wrap; gap: 0.4rem; }
        .profile-skill {
          background: rgba(201,168,76,0.1); border: 1px solid rgba(201,168,76,0.25);
          color: #C9A84C; font-size: 0.74rem; padding: 3px 10px;
          letter-spacing: 0.03em;
        }

        .profile-works-title {
          font-family: 'Noto Serif KR', serif;
          font-size: 1.5rem; font-weight: 300; color: #1A1A2E;
          margin-bottom: 0.5rem;
        }
        .profile-works-line { width: 36px; height: 2px; background: #C9A84C; margin-bottom: 2rem; }
        .profile-work-item {
          background: white; border: 1px solid #E8E4DC;
          padding: 1.6rem; margin-bottom: 0.8rem;
          transition: 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }
        .profile-work-item:hover {
          border-color: rgba(201,168,76,0.4);
          box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        }
        .profile-work-num {
          color: #C9A84C; font-size: 0.7rem; font-weight: 700;
          letter-spacing: 0.15em; margin-bottom: 0.5rem;
        }
        .profile-work-title {
          font-size: 1rem; font-weight: 700; color: #111128; margin-bottom: 0.4rem;
        }
        .profile-work-desc { color: #666; font-size: 0.88rem; line-height: 1.75; }
        .profile-back {
          color: #C9A84C; font-size: 0.82rem; text-decoration: none;
          display: inline-flex; align-items: center; gap: 0.4rem;
          margin-bottom: 2rem; font-weight: 600; transition: opacity 0.15s;
        }
        .profile-back:hover { opacity: 0.7; }

        @media (max-width: 900px) {
          .profile-layout { grid-template-columns: 1fr; gap: 2rem; }
          .profile-card { position: static; }
        }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">TEAM MEMBER</div>
        <h1>{m.name}</h1>
        <p>{m.role}</p>
      </div>

      <div className="section">
        <Link className="profile-back" href="/team">← 구성원 목록으로</Link>

        <div className="profile-layout">
          {/* 왼쪽 카드 */}
          <div className="profile-card">
            <div className="profile-avatar">{m.num}</div>
            <div className="profile-num">MEMBER {m.num}</div>
            <div className="profile-name">{m.name}</div>
            <div className="profile-role">{m.role}</div>

            <div className="profile-divider" />

            <div className="profile-info-row">
              <div className="profile-info-label">GITHUB</div>
              <div className="profile-info-value">
                <a href={`https://github.com/${m.github}`} target="_blank" rel="noopener noreferrer">
                  @{m.github}
                </a>
              </div>
            </div>

            <div className="profile-info-row">
              <div className="profile-info-label">SKILLS</div>
              <div className="profile-skills">
                {m.skills.map(s => (
                  <span key={s} className="profile-skill">{s}</span>
                ))}
              </div>
            </div>
          </div>

          {/* 오른쪽 담당 업무 */}
          <div>
            <div className="profile-works-title">담당 업무</div>
            <div className="profile-works-line" />
            {m.works.map((w, i) => (
              <div className="profile-work-item" key={i}>
                <div className="profile-work-num">0{i + 1}</div>
                <div className="profile-work-title">{w.title}</div>
                <div className="profile-work-desc">{w.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
