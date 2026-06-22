import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '03', name: '김홍익', role: 'Consultation Agent',
    github: 'hongikkim',
    skills: ['Python', 'OpenAI API', 'Streamlit', 'Supabase', 'LangChain', 'PostgreSQL'],
    works: [
      { title: '특허 상담 에이전트', desc: '발명자와의 대화를 통해 문제점·해결수단·효과·구성요소를 단계적으로 수집하는 AI 상담 흐름 설계' },
      { title: '발명 구조화 파이프라인', desc: 'GPT-4o 기반 발명 내용 자동 추출 및 JSON 구조화 (제목·기술분야·배경·효과·알고리즘)' },
      { title: '상담 로그 DB 저장', desc: 'Supabase PostgreSQL 연동으로 상담 이력, 발명 요약, 파일 업로드 결과 영구 저장' },
      { title: 'PDF·HWP 파일 파싱', desc: 'pymupdf·python-docx 활용 발명 관련 문서 자동 텍스트 추출 및 상담 맥락 반영' },
    ],
  }} />
}
