import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

const members = [
  { num: '01', name: '김서현', role: 'Frontend / PatentAI UI', desc: '홈페이지 UI, 다국어 전환, Next.js 화면 구성, 도면 에이전트 연동을 담당합니다.' },
  { num: '02', name: '팀원 2', role: 'Prior Art Agent', desc: '선행기술 조사, 특허 데이터 검색, 유사도 분석 기능을 담당합니다.' },
  { num: '03', name: '팀원 3', role: 'Consultation Agent', desc: '발명 상담 흐름, 상담 로그 구조화, 발명 요약 기능을 담당합니다.' },
  { num: '04', name: '팀원 4', role: 'Specification Agent', desc: '청구항, 명세서 초안, 발명의 효과 및 구성요소 정리 기능을 담당합니다.' },
  { num: '05', name: '팀원 5', role: 'Drawing Agent', desc: '특허 도면 자동 생성, Mermaid 변환, SVG/PNG 렌더링 기능을 담당합니다.' },
  { num: '06', name: '팀원 6', role: 'Review / Integration', desc: '검토 에이전트, 전체 서비스 통합, 테스트 및 발표 자료 정리를 담당합니다.' },
]

export default function TeamPage() {
  return (
    <div className="site">
      <Nav />

      <div className="hero">
        <div className="tag">OUR TEAM</div>
        <h1>구성원 소개</h1>
        <p>PatentAI 프로젝트를 함께 개발하는 팀원을 소개합니다.</p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">PatentAI Team</div>
        <div className="sub">특허 상담, 선행기술 조사, 명세서 작성, 도면 생성, 검토 에이전트를 함께 구축합니다.</div>

        <div className="grid">
          {members.map((m) => (
            <div className="member" key={m.num}>
              <div className="avatar">{m.num}</div>
              <div className="name">{m.name}</div>
              <div className="role">{m.role}</div>
              <div className="desc">{m.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  )
}
