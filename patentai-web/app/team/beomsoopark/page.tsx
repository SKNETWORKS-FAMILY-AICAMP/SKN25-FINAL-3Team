import MemberProfile from '@/components/MemberProfile'

export default function Page() {
  return <MemberProfile m={{
    num: '04', name: '박범수', role: 'Specification / Claims Agent',
    github: 'beomsoopark',
    skills: ['Python', 'sLLM', 'LoRA', 'HuggingFace', 'FastAPI', 'RunPod'],
    works: [
      { title: '청구항 자동 생성 (sLLM)', desc: '특허 명세서 데이터로 파인튜닝한 EXAONE sLLM 모델을 활용한 독립항·종속항 자동 생성' },
      { title: '명세서 초안 작성', desc: '발명 상담 데이터 기반 기술분야·배경기술·발명의 내용·실시예 섹션 자동 초안화' },
      { title: 'RunPod GPU 서버 배포', desc: 'EXAONE-3.0-7.8B 모델을 RunPod에 배포하고 FastAPI REST API로 서비스 제공' },
      { title: 'LoRA 파인튜닝', desc: '한국 특허청 공개 특허 데이터셋을 활용한 청구항 생성 특화 LoRA 어댑터 학습' },
    ],
  }} />
}
