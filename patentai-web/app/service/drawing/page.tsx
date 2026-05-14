import ServiceDetail from '@/components/ServiceDetail'
export default function Page() {
  return <ServiceDetail d={{
    num: '04', tag: 'DRAWING AGENT',
    title: '도면 자동 생성',
    summary: '명세서 텍스트를 분석하여 특허청 실무 수준의 블록도·흐름도·시퀀스 다이어그램을 자동 생성합니다.',
    description: 'PatentAI 도면 에이전트는 GPT-4o-mini로 명세서를 분석하고 SVG 직접 렌더링 방식으로 특허청 제출 기준에 맞는 도면을 생성합니다. 도면부호 자동 배치, 흑백 선화 스타일, 품질 자동 검증까지 포함합니다. 생성된 도면은 SVG 및 고해상도 PNG로 제공됩니다.',
    steps: [
      { num: '01', title: '구성요소 추출', desc: 'GPT-4o-mini로 명세서에서 구성요소와 처리 흐름을 추출합니다.' },
      { num: '02', title: '도면 유형 분류', desc: '발명 유형에 따라 블록도·흐름도·시퀀스·상태도·UI 화면도를 자동 선택합니다.' },
      { num: '03', title: 'SVG 렌더링', desc: '좌표 기반 SVG 렌더러로 도면부호가 포함된 특허청 스타일 도면을 생성합니다.' },
      { num: '04', title: '품질 검증', desc: '100점 만점 품질 점수 산출 및 75점 미만 도면 자동 보정을 수행합니다.' },
    ],
    output: ['SVG 벡터 도면', 'PNG 고해상도 변환본', '품질 점수 및 A~D 등급', '도면 설계 JSON'],
    related: [
      { href: '/service/specification', label: '명세서 작성' },
      { href: '/service/consultation', label: '특허 상담 에이전트' },
      { href: '/service/review', label: '심사 대응' },
    ],
  }} />
}
