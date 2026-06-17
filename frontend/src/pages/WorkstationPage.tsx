// src/pages/WorkstationPage.tsx
import { FormEvent, useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { workspaceApi, WorkstationData, ChatMessage } from '../api/workspace'
import AgentModal, { AgentLog } from '../components/AgentModal'
import ClaimEditModal from '../components/ClaimEditModal'
import ProcessMapModal from '../components/ProcessMapModal'
import PriorArtModal from '../components/PriorArtModal'



const STEP_TO_PIPELINE: Record<string, string> = {
  start: 'summary',
  //log_and_state: currentStep,  // ← 이건 제거
  summary: 'summary',
  claim: 'claim',
  rewrite: 'examiner',
  rewrite_done: 'examiner',
  examiner: 'examiner',
  prior_art_start: 'prior_art',
  prior_art_done: 'prior_art',
  done: 'prior_art',
}

export default function WorkstationPage() {
  const { projectId } = useParams<{ projectId: string }>()
  
  // 상태 관리 (데이터 로딩, 채팅, 에러 등)
  const [data, setData] = useState<WorkstationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatInput, setChatInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const chatBoxRef = useRef<HTMLDivElement>(null)
  const [isClaimModalOpen, setIsClaimModalOpen] = useState(false)
  const [isProcessModalOpen, setIsProcessModalOpen] = useState(false)
  
  // (모달 관리용)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([])
  const [currentStep, setCurrentStep] = useState<string>('summary')
  const [isAgentDone, setIsAgentDone] = useState(false)
 //const [isReportOpen, setIsReportOpen] = useState(false);
  
  const [pendingClaims, setPendingClaims] = useState<any[] | null>(null) // 방금 AI가 만든 저장 대기 중인 청구항
  const [isSaving, setIsSaving] = useState(false)
  const [isDrawingLoading, setIsDrawingLoading] = useState(false)

  const [isPaModalOpen, setIsPaModalOpen] = useState(false) // 
  const [priorArtData, setPriorArtData] = useState<any>(null) //

  const renderMessageContent = (content: string) => {
    // ![alt](url) 패턴을 찾아서 쪼갭니다.
    const parts = content.split(/(!\[.*?\]\(.*?\))/g);

    return parts.map((part, i) => {
      const match = part.match(/!\[(.*?)\]\((.*?)\)/);
      if (match) {
        // 이미지를 찾으면 예쁜 img 태그로 변환!
        return (
          <div key={i} style={{ margin: '16px 0', textAlign: 'center' }}>
            <img 
              src={match[2]} 
              alt={match[1]} 
              style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid var(--lf-border)', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }} 
            />
            <div style={{ fontSize: 11, color: 'var(--lf-muted)', marginTop: 8 }}>{match[1]}</div>
          </div>
        );
      }
      // 이미지가 아니면 그냥 텍스트 출력
      return <span key={i}>{part}</span>;
    });
  }

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
        chat_messages: [...prev.chat_messages, { role: 'assistant', content: res.ai_message }],
        consultation_state: res.extracted_data 
      } : prev)
    } catch (err) {
      alert("메시지 전송 실패")
    } finally {
      setIsSending(false)
    }
  }
  //  "저장해럇!" 버튼 클릭 시 실행
  const handleSaveClaims = async () => {
    if (!pendingClaims || !projectId) return
    setIsSaving(true)
    try {
      await workspaceApi.saveClaims(projectId, pendingClaims)
      alert("저장 완료! 🎉")
      setPendingClaims(null) // 저장이 끝났으니 버튼을 숨깁니다.
      // 최신 상태 리로드
      workspaceApi.getWorkstation(projectId).then(res => setData(res))
    } catch (err) {
      alert("저장에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }
  const [isGenerating, setIsGenerating] = useState(false)
  // 3. 파이프라인 액션 핸들러 (예시: 청구항 작성)
  const handleGenerateClaims = async () => {
    if (isGenerating) return  // ← 추가
    if (!projectId || !confirm("청구항 작성을 시작하시겠습니까?")) return
    // 모달 초기화 및 열기
    setIsGenerating(true) 
    setAgentLogs([{ step: 'system', message: '파이프라인 초기화 중...' }])
    setCurrentStep('summary')
    setIsAgentDone(false)
    setIsModalOpen(true)
    try {
      await workspaceApi.generateClaimsStream(projectId, (data) => {
        console.log('SSE data:', data) // 디버깅용 로그
      // 에러나 경고가 백엔드에서 온 경우 (4대 요소 부족 등)
        if (data.status === 'warning' || data.status === 'error') {
          
          setAgentLogs(prev => [...prev, { step: 'error', message: data.message }])
          setIsAgentDone(true)
          return
        }

        // 실시간 로그와 단계 업데이트
        if (data.step && data.message) {
          setAgentLogs(prev => [...prev, { step: data.step, message: data.message }])
          console.log('setCurrentStep 호출:', STEP_TO_PIPELINE[data.step] ?? data.step) 
          setCurrentStep(STEP_TO_PIPELINE[data.step] ?? data.step)
        }

        // 모든 작업 완료 시
        if (data.step === 'done') {
          setIsAgentDone(true)
          if (data.claims) setPendingClaims(data.claims)
          if (data.prior_art_data) setPriorArtData(data.prior_art_data)
          // 완료되면 최신 데이터(청구항 내역 등)를 서버에서 다시 불러와서 화면 새로고침
          workspaceApi.getWorkstation(projectId).then(res => setData(res))
        }
      })
    } catch (err) {
      setAgentLogs(prev => [...prev, { step: 'error', message: "통신 중 오류가 발생했습니다." }])
      setIsAgentDone(true)
    }finally {
      setIsGenerating(false) 
    }
  }
  // 🎯 명세서 작성 핸들러
  const handleGenerateSpecification = async () => {
    if (!projectId || !confirm("최종 특허 명세서(상세 설명) 작성을 시작하시겠습니까?\n본문 텍스트량이 많아 완료까지 약 1~2분이 소요될 수 있습니다.")) return

    setIsSending(true) // 👈 채팅창 하단에 "AI가 입력 중입니다..." 활성화!

    try {
      const res = await workspaceApi.generateSpecification(projectId)
      
      if (res.status === 'success') {
        alert("최종 명세서 작성이 성공적으로 완료되었습니다! 📄")
        
        // 완료 시 최신 워크스테이션 데이터를 다시 불러와서 
        // AI 변리사가 보낸 명세서 완료 메시지를 채팅창에 즉시 업데이트합니다.
        const updatedData = await workspaceApi.getWorkstation(projectId)
        setData(updatedData)
      } else {
        alert(`명세서 작성 실패: ${res.message}`)
      }
    } catch (err) {
      alert("명세서 작성 중 통신 오류가 발생했습니다.")
    } finally {
      setIsSending(false) // 👈 로딩 종료
    }
  }
  const handleGenerateDrawings = async () => {
    if (!projectId || !confirm("AI 특허 도면(구성도/흐름도) 생성을 시작하시겠습니까?\n이 작업은 최대 1분이 소요될 수 있습니다.")) return

    setIsDrawingLoading(true)
    setIsSending(true) // 채팅창에 "AI가 입력 중입니다..." 띄우기

    try {
      const res = await workspaceApi.generateDrawings(projectId)
      
      if (res.status === 'success') {
        alert("특허 도면 생성 및 저장이 완료되었습니다! 🎨")
        
        // 🚀 핵심: 도면 생성이 완료되면 워크스테이션 데이터를 싹 다시 불러와서 
        // 새 채팅 메시지와 도면 현황을 화면에 즉시 갱신합니다!
        const updatedData = await workspaceApi.getWorkstation(projectId)
        setData(updatedData)
      } else {
        alert(`도면 생성 실패: ${res.message}`)
      }
    } catch (err) {
      alert("도면 생성 중 통신 오류가 발생했습니다.")
    } finally {
      setIsDrawingLoading(false)
      setIsSending(false)
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
            {/* 3. 버튼에 onClick 이벤트 연결! */}
            <button onClick={() => setIsProcessModalOpen(true)} className="btn-line">파이프라인 상태</button>
            <button onClick={handleGenerateClaims} className="btn-gold">청구항 작성</button>
            <button onClick={() => setIsClaimModalOpen(true)} className="btn-line">청구항 수정</button> 
            <button 
              onClick={handleGenerateDrawings} 
              disabled={isDrawingLoading} 
              className="btn-line"
              style={{ opacity: isDrawingLoading ? 0.6 : 1, cursor: isDrawingLoading ? 'not-allowed' : 'pointer' }}
            >
              {isDrawingLoading ? "도면 생성 중..." : "도면 생성"}
            </button>
            <button onClick={handleGenerateSpecification} className="btn-fill">명세서 작성</button>
            <button 
              onClick={() => setIsPaModalOpen(true)} 
              className="btn-action" 
              style={{ background: 'var(--lf-bg2)', border: '1px solid var(--lf-border)', padding: '0 16px', borderRadius: 6, fontSize: 13, fontWeight: 600, color: 'var(--lf-navy)', cursor: 'pointer' }}
            >
              선행기술 리포트
            </button>
          </div>
        </header>

        {/* 채팅 내역 */}
        <div ref={chatBoxRef} style={{ flex: 1, padding: 32, overflowY: 'auto', background: 'var(--lf-bg)', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {chat_messages.map((msg, idx) => (
            <div key={idx} style={{ 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              background: msg.role === 'user' ? 'var(--lf-navy)' : '#fff', // 👈 AI 메시지 배경을 하얗게 하면 도면이 더 돋보입니다.
              color: msg.role === 'user' ? '#fff' : 'var(--lf-navy)',
              border: msg.role === 'assistant' ? '1px solid var(--lf-border)' : 'none',
              padding: '16px 20px', borderRadius: 8, maxWidth: '75%', whiteSpace: 'pre-wrap', fontSize: 14,
              boxShadow: msg.role === 'assistant' ? '0 2px 8px rgba(0,0,0,0.02)' : 'none'
            }}>
              {/* 🎯 그냥 출력하지 않고, 함수를 통과시킵니다! */}
              {renderMessageContent(msg.content)}
            </div>
          ))}
          {isSending && <div style={{ alignSelf: 'flex-start', color: 'var(--lf-muted)', fontSize: 12 }}>AI가 입력 중입니다...</div>}
        </div>

        {pendingClaims && (
            <div style={{ alignSelf: 'flex-end', marginTop: 12, marginBottom: 24 }}>
              <button 
                onClick={handleSaveClaims} 
                disabled={isSaving}
                className="btn-fill" 
                style={{ padding: '12px 24px', fontSize: 13, background: 'var(--lf-navy)', color: '#fff', borderRadius: 8, cursor: 'pointer' }}
              >
                {isSaving ? "저장 중..." : "이 청구항 맘에 들면 저장해럇! 💾"}
              </button>
            </div>
          )}

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

      <AgentModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        logs={agentLogs}
        currentStep={currentStep}
        isDone={isAgentDone}
      />
      <ClaimEditModal 
        isOpen={isClaimModalOpen} 
        onClose={() => setIsClaimModalOpen(false)} 
        projectId={projectId!} 
      />
      
      <ProcessMapModal 
        isOpen={isProcessModalOpen} 
        onClose={() => setIsProcessModalOpen(false)} 
        hasClaims={data?.project.has_claims || false}
        hasDrawings={false} // 나중에 도면 API 연결 시 업데이트
        hasSpec={false}     // 나중에 명세서 API 연결 시 업데이트
      />
      <PriorArtModal 
        isOpen={isPaModalOpen} 
        onClose={() => setIsPaModalOpen(false)} 
        data={priorArtData} 
      />
      {/* <ReportViewer 
        isOpen={isReportOpen} 
        onClose={() => setIsReportOpen(false)} 
        data={data} // 백엔드에서 받아온 전체 데이터를 그대로 던져줍니다!
      /> */}
    </div>
  )
}