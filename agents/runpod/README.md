# agents/runpod

이 폴더는 외부 GPU/RunPod 실행 환경과 연결되는 코드 또는 설정을 분리해두는 영역이다.

## 원칙

- 핵심 graph/state/schema와 외부 실행 환경 의존성을 분리한다.
- 로컬 데모와 배포 실행 경로가 섞이지 않도록 한다.
