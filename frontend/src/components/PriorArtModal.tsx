import React from 'react'

interface Candidate {
  rank: number;
  title: string;
  register_number: string;
  score: number;
  risk_level: 'high' | 'medium' | 'low';
  summary: string;
  pdf_s3_url?: string;
}

interface PriorArtData {
  overall_risk: {
    level: 'high' | 'medium' | 'low';
    summary: string;
  };
  analysis_summary: string;
  candidates: Candidate[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  data?: PriorArtData | null;
}

export default function PriorArtModal({ isOpen, onClose, data }: Props) {
  if (!isOpen) return null

  // 데이터가 아직 없을 때의 화면
  if (!data || !data.candidates) {
    return (
      <div style={overlayStyle}>
        <div style={modalStyle}>
          <Header onClose={onClose} />
          <div className="muted-text" style={{ padding: 60, textAlign: 'center' }}>
            아직 생성된 선행기술조사 리포트가 없습니다.<br/>청구항 작성 파이프라인을 먼저 실행해 주세요.
          </div>
        </div>
      </div>
    )
  }

  // 리스크 레벨에 따른 색상 설정
  const getRiskColor = (level: string) => {
    if (level === 'high') return '#ef4444' // 빨강
    if (level === 'medium') return 'var(--lf-gold)' // 노랑/금색
    return '#059669' // 초록
  }

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <Header onClose={onClose} />

        <div style={{ padding: 32, overflowY: 'auto', flex: 1, background: 'var(--lf-bg)', display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 종합 평가 박스 */}
          <div style={{ 
            background: '#fff', borderLeft: `4px solid ${getRiskColor(data.overall_risk.level)}`, 
            padding: 24, borderRadius: '0 8px 8px 0', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' 
          }}>
            <h3 className="panel-title" style={{ margin: '0 0 12px 0' }}>
              종합 평가: {data.overall_risk.summary}
            </h3>
            <p className="body-text" style={{ margin: 0 }}>
              {data.analysis_summary}
            </p>
          </div>

          <h3 className="panel-title" style={{ margin: '8px 0 0 0' }}>
            검색된 주요 선행문헌 (Top {data.candidates.length})
          </h3>

          {/* 선행문헌 카드 리스트 */}
          {data.candidates.map((cand, idx) => {
            const riskColor = getRiskColor(cand.risk_level)
            
            return (
              <div key={idx} style={{ background: '#fff', border: '1px solid var(--lf-border)', borderRadius: 12, padding: 24 }}>
                <h4 className="card-title" style={{ margin: '0 0 16px 0' }}>
                  [{cand.rank}위] {cand.title}
                </h4>
                
                <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                  <span style={tagStyle}>출원번호: {cand.register_number}</span>
                  <span style={tagStyle}>유사도: {(cand.score * 100).toFixed(1)}%</span>
                  <span style={{ ...tagStyle, color: riskColor, borderColor: riskColor, fontWeight: 600 }}>
                    리스크: {cand.risk_level.toUpperCase()}
                  </span>
                </div>

                <div className="body-text" style={{ background: 'var(--lf-bg2)', padding: 16, borderRadius: 8, marginBottom: 16 }}>
                  <strong style={{ color: 'var(--lf-navy)' }}>💡 AI 핵심 요약:</strong><br/>
                  {cand.summary}
                </div>

                <div style={{ textAlign: 'right' }}>
                  {cand.pdf_s3_url ? (
                    <a 
                      href={cand.pdf_s3_url} 
                      target="_blank" 
                      rel="noreferrer"
                      className="card-title"
                      style={{ display: 'inline-block', background: 'var(--lf-navy)', color: '#fff', padding: '10px 20px', borderRadius: 6, textDecoration: 'none' }}
                    >
                      📄 원문 PDF 열기
                    </a>
                  ) : (
                    <span className="muted-text">🚫 PDF 원문 미제공</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// UI 스타일 헬퍼
const overlayStyle: React.CSSProperties = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1100,
  background: 'rgba(18, 16, 14, 0.4)', backdropFilter: 'blur(4px)',
  display: 'flex', alignItems: 'center', justifyContent: 'center'
}
const modalStyle: React.CSSProperties = {
  background: '#fff', width: 850, maxHeight: '85vh', borderRadius: 16, boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
  display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--lf-border)'
}
const tagStyle: React.CSSProperties = {
  padding: '6px 12px', borderRadius: 20, border: '1px solid var(--lf-border)', color: 'var(--lf-mid)'
}
const Header = ({ onClose }: { onClose: () => void }) => (
  <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <h3 className="panel-title" style={{ margin: 0 }}>AI 선행기술조사 리포트</h3>
    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--lf-mid)' }}>&times;</button>
  </div>
)
