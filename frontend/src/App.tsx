import { Routes, Route, Link } from 'react-router-dom'

function Home() {
  return (
    <div>
      <h1>Patent AI</h1>
      <nav>
        <Link to="/consult">상담 시작</Link>
        {' | '}
        <Link to="/pipeline">특허 파이프라인</Link>
      </nav>
    </div>
  )
}

function ConsultPage() {
  return <div>상담 페이지 — 구현 예정</div>
}

function PipelinePage() {
  return <div>멀티에이전트 파이프라인 — 구현 예정</div>
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/consult" element={<ConsultPage />} />
      <Route path="/pipeline" element={<PipelinePage />} />
    </Routes>
  )
}
