import ServiceDetail from '@/components/ServiceDetail'
export default function Page() {
  return <ServiceDetail d={{
    num: '03', tag: 'SPECIFICATION WRITING',
    title: '명세서 작성',
    summary: '상담 데이터를 바탕으로 청구항·발명의 설명·실시예를 AI가 자동 초안화하여 출원 준비 시간을 대폭 단축합니다.',
    description: 'PatentAI 명세서 에이전트는 특허 데이터로 파인튜닝한 sLLM(EXAONE)을 활용하여 독립항·종속항을 자동 생성합니다. 발명의 설명, 배경기술, 실시예, 도면의 간단한 설명 등 특허법 제42조에서 요구하는 모든 항목을 초안화합니다. AI 초안을 활용하면 변리사 작업 시간이 60~80% 단축됩니다.',
    steps: [
      { num: '01', title: '청구항 생성 (sLLM)', desc: 'EXAONE 파인튜닝 모델로 독립항·종속항을 자동 생성합니다.' },
      { num: '02', title: '발명의 설명 작성', desc: '기술분야·배경기술·발명의 내용·실시예를 자동 초안화합니다.' },
      { num: '03', title: '도면 설명 생성', desc: '도면의 간단한 설명 및 부호의 설명을 자동 작성합니다.' },
      { num: '04', title: '최종 문서 출력', desc: '특허청 표준 형식에 맞는 명세서 초안을 제공합니다.' },
    ],
    output: ['청구항 초안 (독립항·종속항)', '발명의 설명 초안', '실시예 초안', '도면의 간단한 설명'],
    related: [
      { href: '/service/consultation', label: '특허 상담 에이전트' },
      { href: '/service/drawing', label: '도면 자동 생성' },
      { href: '/service/review', label: '심사 대응' },
    ],
  }} />
}
