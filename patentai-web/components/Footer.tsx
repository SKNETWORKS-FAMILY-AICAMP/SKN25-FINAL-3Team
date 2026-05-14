import Link from 'next/link'

export default function Footer() {
  return (
    <footer style={{
      background: '#0A0A16',
      borderTop: '1px solid rgba(201,168,76,0.18)',
      padding: '3.5rem 5rem 2rem',
      color: '#7777A0',
      fontFamily: "'Noto Sans KR', sans-serif",
    }}>
      <style>{`
        .footer-grid {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          gap: 3rem;
          margin-bottom: 2.5rem;
        }
        .footer-logo {
          font-family: 'Noto Serif KR', serif;
          color: #F0EDE6;
          letter-spacing: .2em;
          font-size: 1.1rem;
          margin-bottom: 1rem;
        }
        .footer-logo em { color: #C9A84C; font-style: normal; }
        .footer-desc { font-size: 0.82rem; line-height: 1.8; color: #7777A0; margin-bottom: 1.2rem; }
        .footer-contact { font-size: 0.82rem; line-height: 2; color: #9999B8; }
        .footer-contact a { color: #C9A84C; text-decoration: none; }
        .footer-col-title {
          color: #C9A84C;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.2em;
          margin-bottom: 1rem;
          text-transform: uppercase;
        }
        .footer-links { display: flex; flex-direction: column; gap: 0.55rem; }
        .footer-links a {
          color: #9999B8;
          font-size: 0.82rem;
          text-decoration: none;
          transition: color 0.15s;
        }
        .footer-links a:hover { color: #C9A84C; }
        .footer-bottom {
          border-top: 1px solid rgba(201,168,76,0.12);
          padding-top: 1.5rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.76rem;
          flex-wrap: wrap;
          gap: 0.5rem;
        }
        .footer-badges { display: flex; gap: 1rem; }
        .footer-badge {
          border: 1px solid rgba(201,168,76,0.3);
          color: #C9A84C;
          font-size: 0.7rem;
          padding: 3px 10px;
          letter-spacing: 0.08em;
        }
        @media (max-width: 900px) {
          .footer-grid { grid-template-columns: 1fr 1fr; gap: 2rem; }
          footer { padding: 2.5rem 1.5rem 1.5rem !important; }
          .footer-bottom { flex-direction: column; align-items: flex-start; }
        }
      `}</style>

      <div className="footer-grid">
        {/* 브랜드 */}
        <div>
          <div className="footer-logo">PATENT<em>AI</em></div>
          <div className="footer-desc">
            AI 기반 지식재산 상담 시스템으로<br />
            발명 상담부터 특허 명세서 작성, 도면 생성까지<br />
            전 과정을 자동화합니다.
          </div>
          <div className="footer-contact">
            <div>📍 서울특별시 강남구 테헤란로</div>
            <div>📞 <a href="tel:02-0000-0000">02-0000-0000</a></div>
            <div>✉️ <a href="mailto:contact@patentai.kr">contact@patentai.kr</a></div>
          </div>
        </div>

        {/* 서비스 */}
        <div>
          <div className="footer-col-title">Services</div>
          <div className="footer-links">
            <Link href="/service">특허 상담 에이전트</Link>
            <Link href="/service">선행기술 조사</Link>
            <Link href="/service">명세서 작성</Link>
            <Link href="/service">도면 자동 생성</Link>
            <Link href="/service">심사 대응</Link>
          </div>
        </div>

        {/* 회사 */}
        <div>
          <div className="footer-col-title">Company</div>
          <div className="footer-links">
            <Link href="/service">서비스 소개</Link>
            <Link href="/team">구성원</Link>
            <Link href="/news">소식/자료</Link>
            <Link href="/contact">상담 신청</Link>
          </div>
        </div>

        {/* 고객 */}
        <div>
          <div className="footer-col-title">Client</div>
          <div className="footer-links">
            <Link href="/login/client">고객 로그인</Link>
            <Link href="/login/staff">직원 로그인</Link>
            <Link href="/contact">문의하기</Link>
            <a href="https://www.kipo.go.kr" target="_blank" rel="noopener noreferrer">특허청 바로가기</a>
            <a href="https://www.kipris.or.kr" target="_blank" rel="noopener noreferrer">KIPRIS 바로가기</a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div>© 2026 PatentAI. All rights reserved. · 사업자등록번호 000-00-00000</div>
        <div className="footer-badges">
          <span className="footer-badge">AI PATENT</span>
          <span className="footer-badge">SKN25</span>
        </div>
      </div>
    </footer>
  )
}
