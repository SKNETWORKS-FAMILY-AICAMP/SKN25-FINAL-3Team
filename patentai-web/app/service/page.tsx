import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export default function ServicePage() {
  return (
    <div className="site">
      <Nav />

      <div className="hero">
        <div className="tag">SERVICE OVERVIEW</div>
        <h1>AI 기반 특허 출원 서비스를<br />하나의 흐름으로 제공합니다</h1>
        <p>
          PatentAI는 발명 상담, 선행기술 조사, 명세서 작성, 도면 생성, 검토까지<br />
          특허 출원 전 과정을 자동화하는 지식재산 상담 시스템입니다.
        </p>
      </div>

      <div className="section">
        <div className="line"></div>
        <div className="title">PatentAI 핵심 서비스</div>
        <div className="sub">변리사 업무 흐름을 기준으로 필요한 절차를 단계별 AI 에이전트로 구성했습니다.</div>

        <div className="grid">
          <div className="card">
            <div className="num">01</div>
            <h3>특허 상담 에이전트</h3>
            <p>사용자의 발명 설명을 바탕으로 문제점, 해결수단, 효과, 구성요소를 구조화합니다.</p>
          </div>
          <div className="card">
            <div className="num">02</div>
            <h3>선행기술 조사</h3>
            <p>유사 특허와 기존 기술을 분석하여 신규성 및 진보성 리스크를 빠르게 파악합니다.</p>
          </div>
          <div className="card">
            <div className="num">03</div>
            <h3>명세서 작성</h3>
            <p>청구항, 발명의 설명, 실시예, 도면 설명을 자동으로 초안화합니다.</p>
          </div>
        </div>
      </div>

      <div className="section dark">
        <div className="line"></div>
        <div className="title">서비스 차별점</div>
        <div className="sub">단순 문서 생성이 아니라 특허 실무 프로세스에 맞춘 AI 워크플로우를 제공합니다.</div>

        <div className="grid">
          <div className="card">
            <div className="num">A</div>
            <h3>특허 데이터 기반</h3>
            <p>실제 특허 문서 구조를 기반으로 발명 내용을 정리합니다.</p>
          </div>
          <div className="card">
            <div className="num">B</div>
            <h3>도면 자동화</h3>
            <p>명세서 내용을 분석하여 블록도와 흐름도를 자동 생성합니다.</p>
          </div>
          <div className="card">
            <div className="num">C</div>
            <h3>검토 리포트</h3>
            <p>신규성, 진보성, 기재불비 관점에서 검토 결과를 제공합니다.</p>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
