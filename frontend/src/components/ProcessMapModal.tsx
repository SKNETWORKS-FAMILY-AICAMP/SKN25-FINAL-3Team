import React from 'react'

interface Props {
  isOpen: boolean;
  onClose: () => void;
  // project data에서 현재 상태를 판단할 변수들을 받습니다
  hasClaims: boolean;
  hasDrawings: boolean;
  hasSpec: boolean;
}

export default function ProcessMapModal({ isOpen, onClose, hasClaims, hasDrawings, hasSpec }: Props) {
  if (!isOpen) return null

  const steps = [
    { num: 1, title: '발명 내용 확정', desc: '4대 핵심 요소 파악', done: true },
    { num: 2, title: '특허 청구항 작성', desc: 'AI 독립항/종속항 생성', done: hasClaims },
    { num: 3, title: '도면 생성', desc: '구성도 및 흐름도 도출', done: hasDrawings },
    { num: 4, title: '명세서 본문 작성', desc: '발명의 상세한 설명 완성', done: hasSpec }
  ]
  const activeIndex = steps.findIndex(step => !step.done)
  const currentIndex = activeIndex === -1 ? steps.length - 1 : activeIndex
  const progressWidth = `${(steps.filter(step => step.done).length - 1) * 33.3}%`

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
      background: 'rgba(18, 16, 14, 0.4)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#fff', width: 700, borderRadius: 16, boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--lf-border)'
      }}>
        <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 18, fontFamily: 'var(--lf-serif)' }}>특허 출원 파이프라인 진행도</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--lf-mid)' }}>&times;</button>
        </div>

        <div style={{ padding: '60px 40px', background: 'var(--lf-bg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', position: 'relative' }}>
            {/* 연결선 (진행도에 따라 색상 변경) */}
            <div style={{ position: 'absolute', top: 20, left: 40, right: 40, height: 2, background: 'var(--lf-border)', zIndex: 0 }} />
            <div style={{ position: 'absolute', top: 20, left: 40, width: progressWidth, height: 2, background: '#10b981', zIndex: 0, transition: 'width 0.5s ease-in-out' }} />

            {steps.map((step, idx) => {
              const isDone = step.done;
              const isActive = idx === currentIndex && !isDone;
              
              return (
                <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative', zIndex: 1, width: 120 }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: isDone ? '#10b981' : isActive ? '#f59e0b' : '#fff',
                    border: `2px solid ${isDone ? '#10b981' : isActive ? '#f59e0b' : 'var(--lf-border)'}`,
                    color: isDone || isActive ? '#fff' : 'var(--lf-mid)', fontWeight: 'bold', fontSize: 16, transition: 'all 0.3s'
                  }}>
                    {isDone ? '✓' : step.num}
                  </div>
                  <h4 style={{ marginTop: 16, marginBottom: 4, fontSize: 14, color: isDone ? '#10b981' : isActive ? '#f59e0b' : 'var(--lf-navy)', fontWeight: isDone || isActive ? 600 : 400 }}>{step.title}</h4>
                  <p style={{ margin: 0, fontSize: 11, color: 'var(--lf-muted)', textAlign: 'center' }}>{step.desc}</p>
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ padding: '20px', background: 'var(--lf-bg2)', borderTop: '1px solid var(--lf-border)', textAlign: 'center' }}>
          <p style={{ margin: 0, color: 'var(--lf-mid)', fontSize: 13 }}>
            {activeIndex === -1 ? "모든 과정이 완료되었습니다! 검토 후 출원을 진행해 주세요." : `현재 [${steps[currentIndex].title}] 단계를 진행/대기 중입니다.`}
          </p>
        </div>
      </div>
    </div>
  )
}
