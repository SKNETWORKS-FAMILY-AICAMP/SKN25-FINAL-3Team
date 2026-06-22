import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '06', name: '최현우', role: 'Review / Integration',
    github: 'hyeonwoochoi',
    skills: ['Python', 'Django', 'Docker', 'Supabase', 'GitHub Actions', 'System Integration'],
    works: [
      { title: '전체 파이프라인 통합', desc: '상담→선행기술→명세서→도면→심사 대응까지 전 에이전트를 하나의 파이프라인으로 연결하는 통합 아키텍처 설계' },
      { title: '검토 에이전트', desc: '신규성·진보성·기재불비 관점에서 명세서 품질을 자동 검토하고 개선 방향을 제시하는 AI 리뷰 시스템' },
      { title: 'Django 백엔드', desc: '로그인·JWT 인증·상담 이력 관리·파일 업로드 등 PatentAI 서비스 전반의 백엔드 API 구현' },
      { title: '배포 및 인프라', desc: 'Docker Compose 기반 컨테이너화 및 Supabase 연동, GitHub Actions CI/CD 파이프라인 구성' },
    ],
  }} />
}
