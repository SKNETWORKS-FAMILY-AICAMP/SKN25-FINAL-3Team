import ServiceDetail from '@/components/ServiceDetail'
export default function Page() {
  return <ServiceDetail d={{
    num: '05', tag: 'PATENT REVIEW',
    title: '심사 대응',
    summary: '특허청 거절이유를 AI가 분석하고 의견서 작성 방향과 보정 전략을 제안합니다.',
    description: 'PatentAI 심사 대응 에이전트는 특허청 심사관의 거절이유 통지서를 파싱하여 거절 유형을 분류하고 대응 전략을 제안합니다. 신규성·진보성·기재불비 등 유형별 맞춤 대응 방향과 의견서 초안을 자동 생성하여 변리사의 최종 검토 부담을 줄입니다.',
    steps: [
      { num: '01', title: '거절이유 파싱', desc: '특허청 OA(Office Action) 문서를 자동 파싱하여 거절 항목을 추출합니다.' },
      { num: '02', title: '거절 유형 분류', desc: '신규성·진보성·기재불비·선행기술 등 거절 유형을 AI가 자동 분류합니다.' },
      { num: '03', title: '대응 전략 제안', desc: '유형별 맞춤 의견서 작성 방향 및 청구항 보정 전략을 제안합니다.' },
      { num: '04', title: '의견서 초안 생성', desc: '특허청 제출 형식에 맞는 의견서·보정서 초안을 자동 생성합니다.' },
    ],
    output: ['거절이유 분석 리포트', '의견서 초안', '보정 전략 권고사항', '청구항 보정 제안'],
    related: [
      { href: '/service/prior-art', label: '선행기술 조사' },
      { href: '/service/specification', label: '명세서 작성' },
      { href: '/service/consultation', label: '특허 상담 에이전트' },
    ],
  }} />
}
