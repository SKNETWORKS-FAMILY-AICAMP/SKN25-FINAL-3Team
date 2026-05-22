'use client'

import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function PrivacyPage() {
  const { lang } = useLang()
  const p = t.privacy
  const sections = [
    {
      title: '제1조 (개인정보의 수집 항목 및 수집 방법)',
      body: `PatentAI(이하 "회사")는 아래와 같은 개인정보를 수집합니다.

수집 항목
· 필수: 성명, 이메일 주소, 연락처, 기업/기관명
· 선택: 발명 분야, 기술 분야, 출원 희망 국가
· 자동 수집: IP 주소, 접속 일시, 서비스 이용 기록, 쿠키

수집 방법: 서비스 상담 신청, 회원 가입, AI 상담 에이전트 이용 시 직접 입력 또는 자동 수집`
    },
    {
      title: '제2조 (개인정보의 수집 및 이용 목적)',
      body: `회사는 수집한 개인정보를 다음의 목적에 한하여 이용합니다.

· 특허 상담 서비스 제공 및 AI 에이전트 운영
· 선행기술 조사·명세서 초안 생성 결과 전달
· 서비스 개선 및 신규 서비스 개발
· 법적 의무 이행 및 분쟁 해결`
    },
    {
      title: '제3조 (개인정보의 보유 및 이용 기간)',
      body: `· 서비스 이용 기간 중 보유, 탈퇴 또는 목적 달성 시 즉시 파기
· 관계 법령에 따른 보존 기간: 계약·청약철회 기록 5년, 소비자 불만·분쟁 처리 기록 3년, 접속 기록 1년`
    },
    {
      title: '제4조 (개인정보의 제3자 제공)',
      body: `회사는 이용자의 동의 없이 제3자에게 개인정보를 제공하지 않습니다. 단, 다음의 경우는 예외입니다.

· 이용자가 사전에 동의한 경우
· 법령의 규정 또는 수사기관 요청이 있는 경우`
    },
    {
      title: '제5조 (개인정보 처리 위탁)',
      body: `회사는 서비스 운영을 위해 아래와 같이 개인정보 처리를 위탁합니다.

수탁자: OpenAI (GPT 모델 추론 서비스)
위탁 업무: AI 특허 상담 응답 생성
보유 기간: 위탁 계약 종료 시까지`
    },
    {
      title: '제6조 (이용자의 권리)',
      body: `이용자는 언제든지 다음의 권리를 행사할 수 있습니다.

· 개인정보 열람·정정·삭제 요청
· 개인정보 처리정지 요청
· 동의 철회

요청 방법: contact@patentai.kr 이메일 또는 서면 요청`
    },
    {
      title: '제7조 (개인정보 보호책임자)',
      body: `성명: PatentAI 개인정보보호팀
이메일: privacy@patentai.kr
주소: 서울 서초구 효령로 335 플레이데이터 서초캠퍼스

개인정보 처리에 관한 문의, 불만처리, 피해구제 등을 위한 부서입니다.`
    },
    {
      title: '제8조 (개인정보 보안)',
      body: `회사는 개인정보 보호를 위하여 다음과 같은 기술적·관리적 보호 조치를 취합니다.

· 개인정보의 암호화 (AES-256, TLS 1.3)
· 접근 권한 최소화 및 접근 로그 관리
· 정기적인 보안 취약점 점검`
    },
  ]

  return (
    <div className="site">
      <style>{`
        .legal-wrap { max-width: 900px; margin: 0 auto; padding: 4rem 3rem; }
        .legal-meta { font-size: .78rem; color: #999; margin-bottom: 3rem; border-bottom: 1px solid #E8E4DC; padding-bottom: 1.5rem; display: flex; gap: 2rem; flex-wrap: wrap; }
        .legal-section { margin-bottom: 2.5rem; padding-bottom: 2.5rem; border-bottom: 1px solid #F0EDE8; }
        .legal-section:last-child { border-bottom: none; }
        .legal-h3 { font-family: 'Noto Serif KR', serif; font-size: 1.05rem; font-weight: 400; color: #0A0A16; margin-bottom: 1rem; }
        .legal-body { font-size: .88rem; color: #444; line-height: 2; white-space: pre-line; word-break: keep-all; }
        @media(max-width:768px){ .legal-wrap { padding: 2.5rem 1.5rem; } }
      `}</style>
      <Nav />
      <div className="hero">
        <div className="tag">{tr(p.tag, lang)}</div>
        <h1>{tr(p.h1, lang)}</h1>
        <p>{tr(p.desc, lang)}</p>
      </div>

      <div className="legal-wrap">
        <div className="legal-meta">
          <span>시행일: 2026년 1월 1일</span>
          <span>최종 개정: 2026년 5월 14일</span>
          <span>버전: v2.0</span>
        </div>

        {sections.map((s, i) => (
          <div key={i} className="legal-section">
            <div className="legal-h3">{s.title}</div>
            <div className="legal-body">{s.body}</div>
          </div>
        ))}

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem', flexWrap: 'wrap' }}>
          <Link href="/terms" style={{ fontSize: '.82rem', color: '#C9A84C', textDecoration: 'underline' }}>{tr(p.toTerms, lang)}</Link>
          <Link href="/contact" style={{ fontSize: '.82rem', color: '#888' }}>{tr(p.toContact, lang)}</Link>
        </div>
      </div>

      <Footer />
    </div>
  )
}
