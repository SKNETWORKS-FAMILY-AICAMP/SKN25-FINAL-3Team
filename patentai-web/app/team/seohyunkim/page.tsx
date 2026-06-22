import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '02', name: '김서현', role: 'Frontend / PatentAI UI',
    github: 'bizseohyunkim',
    skills: ['Next.js', 'React', 'TypeScript', 'Streamlit', 'Python', 'SVG 렌더링', 'i18n'],
    works: [
      { title: 'PatentAI 메인 웹사이트', desc: 'Next.js 기반 멀티페이지 웹사이트 구현 (홈·서비스·구성원·소식·상담·FAQ) 및 한/영/일/중 4개국어 i18n 지원' },
      { title: '도면 에이전트 연동', desc: '특허청 실무 수준 SVG 도면 자동 생성 에이전트 개발 및 상담 에이전트 app.py 파이프라인 연결' },
      { title: 'AI 챗봇 위젯', desc: '오른쪽 하단 고정 챗봇 위젯 구현 (키워드 감지 → 관련 페이지 링크 자동 안내, PatentAI 프로필 아바타)' },
      { title: 'Streamlit UI', desc: 'patentai_ui.py 메인 화면 구성 및 발명의 설명 에이전트 연동' },
    ],
  }} />
}
