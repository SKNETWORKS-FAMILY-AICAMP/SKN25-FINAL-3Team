// src/components/AgentModal.tsx
import React, { useEffect, useRef } from 'react'

export interface AgentLog {
  step: string;
  message: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  logs: AgentLog[];
  currentStep: string;
  isDone: boolean;
}

// 각 에이전트 단계별 표시 설정
const PIPELINE_STEPS = [
  { id: 'summary', label: 'Summary Agent', desc: '발명 내용 요약 및 구조화' },
  { id: 'claim', label: 'Claim Draft Agent', desc: '독립항/종속항 초안 작성' },
  { id: 'examiner', label: 'AI Examiner Agent', desc: '명확성 심사 및 거절 사유 검토' },
  { id: 'prior_art', label: 'Prior Art Agent', desc: '선행기술 비교 및 차별성 분석' },
]

export default function AgentModal({ isOpen, onClose, logs, currentStep, isDone }: Props) {
  const logEndRef = useRef<HTMLDivElement>(null)

  

  // 새 로그가 추가될 때마다 자동으로 스크롤 내리기
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
      background: 'rgba(18, 16, 14, 0.4)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#fff', width: 800, borderRadius: 16, boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--lf-border)'
      }}>
        
        {/* 헤더 */}
        <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 18, fontFamily: 'var(--lf-serif)', display: 'flex', alignItems: 'center', gap: 12 }}>
            {!isDone && <span style={{ width: 10, height: 10, background: '#ef4444', borderRadius: '50%', animation: 'pulse 1.5s infinite' }} />}
            {isDone ? '✅ 분석 및 작성 완료' : 'AI 특허 파이프라인 가동 중'}
          </h3>
          {isDone && (
            <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--lf-mid)' }}>&times;</button>
          )}
        </div>

        <div style={{ display: 'flex', height: 460 }}>
          {/* 좌측: 단계 표시 (Stepper) */}
          <div style={{ width: '40%', background: 'var(--lf-bg2)', padding: '32px', borderRight: '1px solid var(--lf-border)' }}>
            <h4 style={{ fontSize: 12, color: 'var(--lf-muted)', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 24 }}>Processing Steps</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {PIPELINE_STEPS.map((step, idx) => {
                const isActive = currentStep === step.id
                const isPassed = PIPELINE_STEPS.findIndex(s => s.id === currentStep) > idx || isDone
                
                return (
                  <div key={step.id} style={{ display: 'flex', gap: 16, opacity: isActive || isPassed ? 1 : 0.4, transition: 'opacity 0.3s' }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: isActive ? 'var(--lf-gold)' : isPassed ? 'var(--lf-navy)' : '#fff',
                      border: `1px solid ${isActive || isPassed ? 'transparent' : 'var(--lf-border)'}`,
                      color: '#fff', fontSize: 12, fontWeight: 'bold'
                    }}>
                      {isPassed ? '✓' : idx + 1}
                    </div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: isActive ? 600 : 400, color: isActive ? 'var(--lf-gold)' : 'var(--lf-navy)' }}>{step.label}</div>
                      <div style={{ fontSize: 12, color: 'var(--lf-mid)', marginTop: 2 }}>{step.desc}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* 우측: 실시간 작업 로그 */}
          <div style={{ width: '60%', padding: '32px', overflowY: 'auto', background: '#fff', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h4 style={{ fontSize: 12, color: 'var(--lf-muted)', textTransform: 'uppercase', letterSpacing: 1.5, marginBottom: 8 }}>Live Log</h4>
            {logs.map((log, idx) => (
              <div key={idx} style={{ 
                fontSize: 13, color: log.step === 'error' ? '#ef4444' : 'var(--lf-body)', 
                background: 'var(--lf-bg2)', padding: '12px 16px', borderRadius: 8, lineHeight: 1.5
              }}>
                {log.message}
              </div>
            ))}
            {!isDone && (
              <div style={{ fontSize: 13, color: 'var(--lf-mid)', fontStyle: 'italic', padding: '12px 16px' }}>
                AI가 데이터를 처리하고 있습니다...
              </div>
            )}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* 푸터 */}
        {isDone && (
          <div style={{ padding: '16px 32px', background: 'var(--lf-bg2)', borderTop: '1px solid var(--lf-border)', textAlign: 'right' }}>
            <button onClick={onClose} className="btn-fill" style={{ padding: '10px 24px' }}>확인 후 창 닫기</button>
          </div>
        )}
      </div>
    </div>
  )
}