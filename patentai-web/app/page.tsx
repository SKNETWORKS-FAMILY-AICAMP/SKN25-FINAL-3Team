import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'

export default function Home() {
  return (
    <div className="site">
      <Nav />

      {/* HERO */}
      <div className="hero home">
        <img className="hero-img img1"
          src="https://upload.wikimedia.org/wikipedia/commons/3/3f/N_Seoul_Tower_%2813952097192%29.jpg"
          alt="서울 N타워" />
        <img className="hero-img img2"
          src="https://upload.wikimedia.org/wikipedia/commons/5/5b/Lotte_World_Tower_from_Olympic_Park.jpg"
          alt="롯데월드타워" />
        <img className="hero-img img3"
          src="https://upload.wikimedia.org/wikipedia/commons/5/51/Statue_of_King_Sejong_and_Gwanghwamun_Square.jpg"
          alt="광화문" />

        <div className="hero-content">
          <div className="tag">AI-POWERED PATENT CONSULTATION SYSTEM</div>
          <h1>발명의 가치를<br />권리로 만들어 드립니다</h1>
          <div className="line"></div>
          <p>
            발명 내용을 자유롭게 설명해 주시면<br />
            AI가 특허 출원에 필요한 정보를 체계적으로 구조화해 드립니다
          </p>
          <Link className="btn" href="/service">서비스 살펴보기 →</Link>
        </div>
      </div>

      {/* STATS */}
      <div className="stats">
        <div className="stat"><b>1,240+</b><p>처리 특허 건수</p></div>
        <div className="stat"><b>98.2%</b><p>고객 만족도</p></div>
        <div className="stat"><b>12</b><p>AI 전문 모델</p></div>
        <div className="stat"><b>542+</b><p>학습 특허 데이터</p></div>
      </div>

      {/* 주요 서비스 */}
      <div className="section">
        <div className="sec-line"></div>
        <div className="sec-title">주요 서비스</div>
        <div className="sec-sub">AI 기반 특허 출원 전 과정을 지원합니다.</div>

        <div className="grid">
          <Link href="/service">
            <div className="card">
              <div className="num">01</div>
              <h3>선행기술 조사</h3>
              <p>발명 내용을 기반으로 유사 특허와 선행기술을 자동으로 탐색합니다.</p>
            </div>
          </Link>
          <Link href="/service">
            <div className="card">
              <div className="num">02</div>
              <h3>명세서 작성</h3>
              <p>청구항, 발명의 설명, 도면 설명을 구조화하여 초안을 생성합니다.</p>
            </div>
          </Link>
          <Link href="/service">
            <div className="card">
              <div className="num">03</div>
              <h3>도면 에이전트</h3>
              <p>특허 명세서를 분석하여 블록도와 흐름도를 자동 생성합니다.</p>
            </div>
          </Link>
        </div>
      </div>

      {/* 업무 흐름 */}
      <div className="section dark">
        <div className="sec-line"></div>
        <div className="sec-title">PatentAI 업무 흐름</div>
        <div className="sec-sub">발명 상담부터 도면 생성과 검토까지 하나의 흐름으로 연결합니다.</div>

        <div className="workflow">
          <div className="step"><b>01</b><p>발명 내용 입력</p></div>
          <div className="step"><b>02</b><p>AI 구조화</p></div>
          <div className="step"><b>03</b><p>선행기술 분석</p></div>
          <div className="step"><b>04</b><p>명세서/도면 생성</p></div>
          <div className="step"><b>05</b><p>검토 및 리포트</p></div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
