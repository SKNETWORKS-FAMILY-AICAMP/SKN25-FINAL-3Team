import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '05', name: '조은석', role: 'Drawing Agent',
    github: 'eunseokjo',
    skills: ['Python', 'SVG', 'OpenAI Vision', 'cairosvg', 'Pillow', 'Patent Drawing'],
    works: [
      { title: '특허 도면 자동 생성 에이전트', desc: '명세서 텍스트 분석 후 블록도·흐름도·시퀀스·상태도·UI 화면도 등 5종 SVG 도면 자동 생성' },
      { title: '특허청 실무 SVG 렌더러', desc: '도면부호(참조번호) 자동 배치, 흑백 선화 스타일, 특허청 제출 기준 형식 준수 렌더링 엔진 구현' },
      { title: '도면 품질 자동 검증', desc: '도면부호 완비 여부·구성요소 수·레이아웃 품질을 자동 채점하는 100점 만점 품질 시스템' },
      { title: 'Vision 검수 시스템', desc: 'GPT-4o Vision API를 활용한 생성 도면 자동 검수 및 개선 제안 파이프라인' },
    ],
  }} />
}
