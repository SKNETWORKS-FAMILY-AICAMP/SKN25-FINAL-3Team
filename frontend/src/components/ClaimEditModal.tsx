import React, { useEffect, useState } from 'react'
import { workspaceApi } from '../api/workspace'

interface Claim {
  id: number;
  claim_no: number;
  is_dependent: boolean;
  category: string;
  cited_claim_no: number[];
  content: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export default function ClaimEditModal({ isOpen, onClose, projectId }: Props) {
  const [claims, setClaims] = useState<Claim[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // 모달이 열릴 때마다 백엔드에서 최신 청구항을 불러옵니다.
  useEffect(() => {
    if (isOpen && projectId) {
      setIsLoading(true)
      workspaceApi.getClaims(projectId)
        .then(res => {
          if (res.status === 'success') setClaims(res.claims)
          else setClaims([])
        })
        .catch(err => console.error(err))
        .finally(() => setIsLoading(false))
    }
  }, [isOpen, projectId])

  // 텍스트 수정 핸들러
  const handleChange = (id: number, newContent: string) => {
    setClaims(prev => prev.map(c => c.id === id ? { ...c, content: newContent } : c))
  }

  // 저장 버튼 핸들러
  const handleSave = async () => {
    setIsSaving(true)
    try {
      await workspaceApi.updateClaims(projectId, claims)
      alert("청구항 수정이 완료되었습니다! 💾")
      onClose() // 저장 완료 후 모달 닫기
    } catch (err) {
      alert("수정 실패: 통신 에러")
    } finally {
      setIsSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 1000,
      background: 'rgba(18, 16, 14, 0.4)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: '#fff', width: 800, maxHeight: '85vh', borderRadius: 16, boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden', border: '1px solid var(--lf-border)'
      }}>
        <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="panel-title" style={{ margin: 0 }}>특허 청구범위 수정</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 24, cursor: 'pointer', color: 'var(--lf-mid)' }}>&times;</button>
        </div>

        <div style={{ padding: 32, overflowY: 'auto', flex: 1, background: 'var(--lf-bg)', display: 'flex', flexDirection: 'column', gap: 24 }}>
          {isLoading ? (
            <p className="muted-text" style={{ textAlign: 'center', padding: '40px 0' }}>데이터를 불러오는 중입니다...</p>
          ) : claims.length === 0 ? (
            <p className="muted-text" style={{ textAlign: 'center', padding: '40px 0' }}>아직 저장된 청구항이 없습니다.</p>
          ) : (
            claims.map((claim) => (
              <div key={claim.id} style={{ background: '#fff', border: '1px solid var(--lf-border)', borderRadius: 8, padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <strong className="card-title" style={{ color: 'var(--lf-gold)' }}>
                    {`[청구항 ${claim.claim_no}]`} {claim.is_dependent ? `(종속항 - ${claim.category})` : `(독립항 - ${claim.category})`}
                  </strong>
                </div>
                <textarea 
                  value={claim.content} 
                  onChange={(e) => handleChange(claim.id, e.target.value)}
                  className="input-area"
                  style={{ height: 120, resize: 'vertical' }}
                />
              </div>
            ))
          )}
        </div>

        <div style={{ padding: '16px 32px', background: 'var(--lf-bg2)', borderTop: '1px solid var(--lf-border)', textAlign: 'right' }}>
          <button onClick={handleSave} disabled={isSaving || claims.length === 0} className="btn-fill" style={{ padding: '10px 24px', opacity: isSaving ? 0.7 : 1 }}>
            {isSaving ? '저장 중...' : '수정된 내용 저장'}
          </button>
        </div>
      </div>
    </div>
  )
}
