import ServiceDetail from '@/components/ServiceDetail'
export default function Page() {
  return <ServiceDetail d={{
    num: '01', tag: 'CONSULTATION AGENT',
    title: '특허 상담 에이전트',
    summary: '발명자와의 대화를 통해 문제점·해결수단·효과·구성요소를 체계적으로 구조화하는 AI 상담 시스템입니다.',
    description: 'PatentAI 상담 에이전트는 GPT-4o 기반 대화형 인터페이스로 발명 내용을 단계적으로 수집합니다. 기술적 배경 없이도 발명 아이디어를 명확하게 정리할 수 있으며, 상담 결과는 특허 명세서 작성의 기초 데이터로 활용됩니다. PDF·HWP·DOCX 파일 업로드도 지원합니다.',
    steps: [
      { num: '01', title: '발명 내용 입력', desc: '발명의 배경, 문제점, 해결 방법을 자유롭게 설명합니다.' },
      { num: '02', title: 'AI 구조화', desc: 'GPT-4o가 발명 내용을 문제점·해결수단·효과·구성요소로 자동 분류합니다.' },
      { num: '03', title: '알고리즘 수집', desc: '소프트웨어·방법 발명의 경우 단계별 알고리즘을 체계적으로 수집합니다.' },
      { num: '04', title: '최종 요약 확인', desc: '구조화된 발명 내용을 검토하고 DB에 저장합니다.' },
    ],
    output: ['발명 구조화 JSON', '청구항 초안 기초 데이터', '상담 리포트', 'Supabase DB 저장'],
    related: [
      { href: '/service/prior-art', label: '선행기술 조사' },
      { href: '/service/specification', label: '명세서 작성' },
      { href: '/service/drawing', label: '도면 자동 생성' },
    ],
  }} />
}
