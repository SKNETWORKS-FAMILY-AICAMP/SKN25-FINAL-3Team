import { useEffect, useState } from 'react'

interface PatentResult {
  id: string
  title: string
  applicant: string
  applicationNumber: string
  date: string
  abstract: string
}

interface Props {
  isOpen: boolean
  query: string
  onClose: () => void
}

export default function PatentSearchModal({ isOpen, query, onClose }: Props) {
  const [selected, setSelected] = useState<PatentResult | null>(null)
  const [results, setResults] = useState<PatentResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')


  useEffect(() => {
    if (!isOpen || !query) return
    setIsLoading(true)
    setError('')
    setSelected(null)
    fetch(`/api/v1/patent-search?query=${encodeURIComponent(query)}`)
      .then(async res => {
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data?.detail?.message || '특허 검색 요청에 실패했습니다.')
        }
        if (!Array.isArray(data)) {
          throw new Error('특허 검색 응답 형식이 올바르지 않습니다.')
        }
        setResults(data)
      })
      .catch(err => {
        setResults([])
        setError(err instanceof Error ? err.message : '특허 검색 중 오류가 발생했습니다.')
      })
    .finally(() => setIsLoading(false))
  }, [isOpen, query])


  if (!isOpen) return null

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 700,
      background: 'rgba(18,16,14,0.4)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      paddingTop: 90,
    }} onClick={onClose}>
      <div style={{
        background: '#fff', width: 800, maxHeight: '75vh', borderRadius: 16,
        border: '1px solid var(--lf-border)', boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>

        {/* 헤더 */}
        <div style={{ padding: '20px 28px', borderBottom: '1px solid var(--lf-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <span style={{ fontSize: 13, color: 'var(--lf-muted)' }}>
              "<strong style={{ color: 'var(--lf-navy)' }}>{query}</strong>" 검색 결과 {results.length}건
            </span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: 'var(--lf-mid)' }}>&times;</button>
        </div>

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* 결과 리스트 */}
          <div style={{ width: selected ? '45%' : '100%', overflowY: 'auto', borderRight: selected ? '1px solid var(--lf-border)' : 'none', transition: 'width 0.2s' }}>
            {isLoading && (
              <div style={{ padding: '32px 28px', color: 'var(--lf-muted)', fontSize: 13 }}>
                검색 중...
              </div>
            )}
            {!isLoading && error && (
              <div style={{ padding: '32px 28px', color: '#dc2626', fontSize: 13, lineHeight: 1.7 }}>
                {error}
              </div>
            )}
            {!isLoading && !error && results.length === 0 && (
              <div style={{ padding: '32px 28px', color: 'var(--lf-muted)', fontSize: 13 }}>
                검색 결과가 없습니다.
              </div>
            )}
            {results.map(result => (
              <div
                key={result.id || result.applicationNumber}
                onClick={() => setSelected(result)}
                style={{
                  padding: '20px 28px', borderBottom: '1px solid var(--lf-border)', cursor: 'pointer',
                  background: selected?.id === result.id ? 'var(--lf-bg2)' : '#fff',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={e => { if (selected?.id !== result.id) e.currentTarget.style.background = 'var(--lf-bg2)' }}
                onMouseLeave={e => { if (selected?.id !== result.id) e.currentTarget.style.background = '#fff' }}
              >
                <p style={{ fontSize: 15, fontWeight: 500, color: 'var(--lf-navy)', marginBottom: 6 }}>{result.title}</p>
                <div style={{ display: 'flex', gap: 12, marginBottom: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--lf-gold)' }}>{result.applicant}</span>
                  <span style={{ fontSize: 12, color: 'var(--lf-muted)' }}>{result.applicationNumber}</span>
                  <span style={{ fontSize: 12, color: 'var(--lf-muted)' }}>{result.date}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--lf-mid)', lineHeight: 1.6, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as any }}>
                  {result.abstract}
                </p>
              </div>
            ))}
          </div>

          {/* 상세 보기 */}
          {selected && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
              <h3 style={{ fontSize: 17, fontWeight: 500, color: 'var(--lf-navy)', marginBottom: 16, lineHeight: 1.5 }}>{selected.title}</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
                {[['출원인', selected.applicant], ['출원번호', selected.applicationNumber], ['출원일', selected.date]].map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', gap: 12 }}>
                    <span style={{ fontSize: 12, color: 'var(--lf-muted)', width: 60, flexShrink: 0 }}>{k}</span>
                    <span style={{ fontSize: 13, color: 'var(--lf-navy)' }}>{v}</span>
                  </div>
                ))}
              </div>
              <div style={{ borderTop: '1px solid var(--lf-border)', paddingTop: 16 }}>
                <p style={{ fontSize: 12, color: 'var(--lf-muted)', marginBottom: 8 }}>요약</p>
                <p style={{ fontSize: 14, color: 'var(--lf-body)', lineHeight: 1.8 }}>{selected.abstract}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
