import ServiceDetail from '@/components/ServiceDetail'
export default function Page() {
  return <ServiceDetail d={{
    num: '02', tag: 'PRIOR ART SEARCH',
    title: '선행기술 조사',
    summary: 'KIPRIS·USPTO·EPO 등 주요국 특허 DB를 AI 벡터 검색으로 분석하여 신규성·진보성 위험을 사전에 파악합니다.',
    description: '선행기술 조사는 특허 출원 전 반드시 거쳐야 하는 핵심 단계입니다. PatentAI는 단순 키워드 검색이 아닌 임베딩 벡터 유사도와 키워드 하이브리드 검색(RRF)을 결합하여 더 정확한 관련 특허를 탐색합니다. IPC 코드별 대량 수집 후 관련도 순으로 랭킹하여 출원 전략 수립에 활용합니다.',
    steps: [
      { num: '01', title: '키워드 생성', desc: '발명 내용에서 핵심 기술 키워드와 IPC 분류 코드를 자동 추출합니다.' },
      { num: '02', title: '특허 DB 수집', desc: 'KIPRIS·USPTO·EPO에서 IPC 코드별 관련 특허를 대량 수집합니다.' },
      { num: '03', title: '벡터 유사도 검색', desc: '임베딩 모델로 특허 텍스트를 벡터화하고 코사인 유사도를 산출합니다.' },
      { num: '04', title: '리포트 생성', desc: '유사도 점수, 위험도 등급, 출원 전략 권고를 담은 리포트를 생성합니다.' },
    ],
    output: ['유사 특허 TOP-N 목록', '유사도 점수 (0~1)', '신규성·진보성 위험도 등급', '출원 전략 권고 리포트'],
    related: [
      { href: '/service/consultation', label: '특허 상담 에이전트' },
      { href: '/service/specification', label: '명세서 작성' },
      { href: '/service/review', label: '심사 대응' },
    ],
  }} />
}
