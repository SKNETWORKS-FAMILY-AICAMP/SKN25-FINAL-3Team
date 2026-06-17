// src/pages/WorkstationPage.tsx
import { FormEvent, useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { workspaceApi, WorkstationData, ChatMessage } from '../api/workspace'
// import AgentModal from '../components/AgentModal' // 모달은 다음 스텝에서 분리!

export default function WorkstationPage() {
  const { projectId } = useParams<{ projectId: string }>()
  
  // 상태 관리 (데이터 로딩, 채팅, 에러 등)
  const [data, setData] = useState<WorkstationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatInput, setChatInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const chatBoxRef = useRef<HTMLDivElement>(null)

  // 1. 초기 데이터 로드
  useEffect(() => {
    if (!projectId) return
    workspaceApi.getWorkstation(projectId)
      .then(res => setData(res))
      .catch(err => alert("데이터를 불러오는데 실패했습니다: " + err.message))
      .finally(() => setLoading(false))
  }, [projectId])

  // 스크롤 맨 아래로 자동 이동
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
    }
  }, [data?.chat_messages])

  // 2. 채팅 전송 핸들러
  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || !projectId || !data) return

    const newMessage = chatInput
    setChatInput('')
    setIsSending(true)

    // 낙관적 UI 업데이트 (사용자 메시지 먼저 화면에 띄우기)
    const newChat: ChatMessage = { role: 'user', content: newMessage }
    setData({ ...data, chat_messages: [...data.chat_messages, newChat] })

    try {
      const res = await workspaceApi.sendMessage(projectId, newMessage)
      // AI 응답 추가
      setData(prev => prev ? {
        ...prev,
        chat_messages: [...prev.chat_messages, { role: 'assistant', content: res.reply }]
      } : prev)
    } catch (err) {
      alert("메시지 전송 실패")
    } finally {
      setIsSending(false)
    }
  }

  // 3. 파이프라인 액션 핸들러 (예시: 청구항 작성)
  const handleGenerateClaims = async () => {
    if (!projectId || !confirm("청구항 작성을 시작하시겠습니까?")) return
    try {
      await workspaceApi.generateClaims(projectId)
      alert("AI가 청구항 작성을 시작했습니다.")
      // TODO: Agent Modal 띄우기 로직 추가
    } catch (err) {
      alert("오류가 발생했습니다.")
    }
  }

  if (loading) return <div style={{ padding: 100, textAlign: 'center' }}>데이터 로딩 중...</div>
  if (!data) return <div style={{ padding: 100, textAlign: 'center' }}>프로젝트를 찾을 수 없습니다.</div>

  const { project, invention_input, consultation_state, chat_messages } = data

  return (
    <div className="lf-ws-container" style={{ display: 'flex', minHeight: '100vh', paddingTop: 70 }}>
      
      {/* 왼쪽 사이드바 (원본 데이터) */}
      <aside className="lf-ws-sidebar" style={{ width: 400, borderRight: '1px solid var(--lf-border)', background: 'var(--lf-bg2)', padding: 24, overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, fontFamily: 'var(--lf-serif)' }}>발명 원본 데이터</h2>
          <Link to={`/report/${project.id}`} target="_blank" className="btn-line" style={{ padding: '6px 12px', fontSize: 10 }}>리포트 보기</Link>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* 1. 해결하고자 하는 과제 */}
          <div className="card-sm">
            <h3 style={{ fontSize: 12, color: 'var(--lf-gold)', marginBottom: 8 }}>1. 해결하고자 하는 과제</h3>
            <p style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{invention_input.problem_to_solve}</p>
          </div>
          
          {/* 2. 종래 기술의 문제점 */}
          <div className="card-sm">
            <h3 style={{ fontSize: 12, color: 'var(--lf-gold)', marginBottom: 8 }}>2. 종래 기술의 문제점</h3>
            <p style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{invention_input.prior_art_problem}</p>
          </div>

          {/* 3. 핵심 기술 구성 */}
          <div className="card-sm">
            <h3 style={{ fontSize: 12, color: 'var(--lf-gold)', marginBottom: 8 }}>3. 핵심 기술 구성</h3>
            <p style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{invention_input.core_tech}</p>
          </div>

          {/* 4. 기대 효과 */}
          <div className="card-sm">
            <h3 style={{ fontSize: 12, color: 'var(--lf-gold)', marginBottom: 8 }}>4. 기대 효과</h3>
            <p style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{invention_input.expected_effect || "(입력되지 않음)"}</p>
          </div>

          {/* AI Agent Analysis (이하 동일) */}
          <div style={{ marginTop: 32 }}>
            <h2 style={{ fontSize: 16, fontFamily: 'var(--lf-serif)', marginBottom: 16 }}>AI Agent Analysis</h2>
            <div className="card-sm" style={{ background: '#fff' }}>
               <h4 style={{ fontSize: 11, color: 'var(--lf-mid)', marginBottom: 4 }}>추출된 핵심 문제점</h4>
               <p style={{ fontSize: 13 }}>{consultation_state.ext_problem || "분석 대기 중..."}</p>
            </div>
            
            <div className="card-sm" style={{ background: '#fff', marginTop: 12 }}>
               <h4 style={{ fontSize: 11, color: 'var(--lf-mid)', marginBottom: 4 }}>추출된 해결 방법</h4>
               <p style={{ fontSize: 13 }}>{consultation_state.ext_solution || "분석 대기 중..."}</p>
            </div>
            
            <div className="card-sm" style={{ background: '#fff', marginTop: 12 }}>
               <h4 style={{ fontSize: 11, color: 'var(--lf-mid)', marginBottom: 4 }}>추출된 차별성</h4>
               <p style={{ fontSize: 13 }}>{consultation_state.ext_differentiation || "분석 대기 중..."}</p>
            </div>
            
            <div className="card-sm" style={{ background: '#fff', marginTop: 12 }}>
               <h4 style={{ fontSize: 11, color: 'var(--lf-mid)', marginBottom: 4 }}>추출된 기대 효과</h4>
               <p style={{ fontSize: 13 }}>{consultation_state.ext_effect || "분석 대기 중..."}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* 오른쪽 메인 (액션 버튼 & 채팅창) */}
      <main className="lf-ws-main" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <header style={{ padding: '24px 32px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: 24, fontFamily: 'var(--lf-serif)', margin: 0 }}>{project.title}</h2>
          
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-line">파이프라인 상태</button>
            <button onClick={handleGenerateClaims} className="btn-gold">청구항 작성</button>
            <button className="btn-line">도면 생성</button>
            <button className="btn-fill">명세서 작성</button>
          </div>
        </header>

        {/* 채팅 내역 */}
        <div ref={chatBoxRef} style={{ flex: 1, padding: 32, overflowY: 'auto', background: 'var(--lf-bg)', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {chat_messages.map((msg, idx) => (
            <div key={idx} style={{ 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              background: msg.role === 'user' ? 'var(--lf-navy)' : 'var(--lf-bg2)',
              color: msg.role === 'user' ? '#fff' : 'var(--lf-navy)',
              border: msg.role === 'assistant' ? '1px solid var(--lf-border)' : 'none',
              padding: '16px 20px', borderRadius: 8, maxWidth: '70%', whiteSpace: 'pre-wrap', fontSize: 14
            }}>
              {msg.content}
            </div>
          ))}
          {isSending && <div style={{ alignSelf: 'flex-start', color: 'var(--lf-muted)', fontSize: 12 }}>AI가 입력 중입니다...</div>}
        </div>

        {/* 채팅 입력 폼 */}
        <footer style={{ padding: 24, borderTop: '1px solid var(--lf-border)', background: 'var(--lf-bg2)' }}>
          <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: 12 }}>
            <button type="button" className="btn-line" style={{ padding: '0 20px' }}>📎</button>
            <input 
              type="text" 
              value={chatInput} 
              onChange={e => setChatInput(e.target.value)} 
              disabled={isSending}
              placeholder="발명에 대해 AI 변리사에게 자유롭게 설명해 주세요..." 
              className="input-field" 
              style={{ flex: 1, background: '#fff', borderRadius: 4, padding: '0 20px', border: '1px solid var(--lf-border)' }} 
            />
            <button type="submit" disabled={isSending} className="btn-gold" style={{ padding: '0 32px' }}>전송</button>
          </form>
        </footer>
      </main>

      {/* TODO: 여기에 나중에 AgentModal 추가 */}
    </div>
  )
}