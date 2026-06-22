import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '01', name: '권가영', role: 'Prior Art Agent',
    github: 'gayeongkwon',
    skills: ['Python', 'Elasticsearch', 'KIPRIS API', 'Vector DB', 'RAG', 'FastAPI'],
    works: [
      { title: '선행기술 조사 에이전트', desc: 'KIPRIS·USPTO·EPO 특허 데이터베이스 기반 선행기술 자동 조사 파이프라인 구현' },
      { title: '벡터 유사도 검색', desc: '임베딩 모델을 활용한 특허 텍스트 벡터화 및 코사인 유사도 기반 관련 특허 탐색' },
      { title: '하이브리드 검색 시스템', desc: '키워드 검색과 벡터 검색을 결합한 RRF(Reciprocal Rank Fusion) 하이브리드 검색 구현' },
      { title: '신규성·진보성 리포트', desc: '유사도 점수, 위험도 등급, 출원 전략 권고사항을 포함한 선행기술 분석 리포트 생성' },
    ],
  }} />
}
