'use client'

import { useState, useRef, useEffect } from 'react'

type Message = { role: 'user' | 'bot'; text: string }

const GREET = '안녕하세요! PatentAI 상담 도우미입니다.\n발명 내용이나 특허 관련 궁금한 점을 자유롭게 말씀해 주세요.'

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([{ role: 'bot', text: GREET }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text }])
    setLoading(true)
    try {
      // 상담 에이전트 백엔드 연결 (apps/streamlit 또는 별도 API 구성 전까지 안내 메시지)
      setMessages(prev => [...prev, {
        role: 'bot',
        text: `"${text}"에 대해 검토 중입니다.\n\n더 자세한 상담은 전문 상담 에이전트를 통해 진행해 드립니다. 상담 신청 페이지로 이동하시겠어요?`,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <style>{`
        .chat-fab {
          position: fixed;
          bottom: 2rem;
          right: 2rem;
          width: 58px;
          height: 58px;
          background: #111128;
          border: 2px solid #C9A84C;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          z-index: 9999;
          box-shadow: 0 8px 24px rgba(0,0,0,0.3);
          transition: transform 0.2s, background 0.2s;
        }
        .chat-fab:hover { background: #C9A84C; transform: scale(1.08); }
        .chat-fab svg { width: 26px; height: 26px; }

        .chat-panel {
          position: fixed;
          bottom: 6rem;
          right: 2rem;
          width: 360px;
          height: 500px;
          background: #fff;
          border: 1px solid #E8E4DC;
          box-shadow: 0 24px 60px rgba(0,0,0,0.18);
          display: flex;
          flex-direction: column;
          z-index: 9998;
          animation: slideUp 0.22s ease;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .chat-header {
          background: #111128;
          padding: 1rem 1.2rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 2px solid #C9A84C;
        }
        .chat-header-title {
          color: #F0EDE6;
          font-size: 0.95rem;
          font-weight: 700;
          letter-spacing: 0.05em;
        }
        .chat-header-title em { color: #C9A84C; font-style: normal; }
        .chat-close {
          background: none;
          border: none;
          color: #888;
          font-size: 1.3rem;
          cursor: pointer;
          line-height: 1;
          padding: 0;
        }
        .chat-close:hover { color: #C9A84C; }

        .chat-messages {
          flex: 1;
          overflow-y: auto;
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
          background: #FAFAFA;
        }
        .chat-bubble {
          max-width: 82%;
          padding: 0.7rem 1rem;
          font-size: 0.88rem;
          line-height: 1.6;
          white-space: pre-wrap;
        }
        .chat-bubble.bot {
          background: #fff;
          border: 1px solid #E8E4DC;
          color: #333;
          align-self: flex-start;
          border-radius: 0 12px 12px 12px;
        }
        .chat-bubble.user {
          background: #111128;
          color: #F0EDE6;
          align-self: flex-end;
          border-radius: 12px 12px 0 12px;
        }
        .chat-typing {
          align-self: flex-start;
          color: #999;
          font-size: 0.82rem;
          padding: 0.4rem 0;
        }

        .chat-input-row {
          display: flex;
          border-top: 1px solid #E8E4DC;
          background: #fff;
        }
        .chat-input {
          flex: 1;
          border: none;
          padding: 0.9rem 1rem;
          font-size: 0.88rem;
          outline: none;
          background: transparent;
          font-family: inherit;
        }
        .chat-send {
          background: none;
          border: none;
          padding: 0 1rem;
          cursor: pointer;
          color: #C9A84C;
          font-size: 1.2rem;
          transition: color 0.15s;
        }
        .chat-send:hover { color: #111128; }
        .chat-send:disabled { color: #ccc; cursor: default; }

        @media (max-width: 480px) {
          .chat-panel { width: calc(100vw - 2rem); right: 1rem; bottom: 5rem; }
          .chat-fab { bottom: 1rem; right: 1rem; }
        }
      `}</style>

      {/* 챗봇 패널 */}
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <span className="chat-header-title">PATENT<em>AI</em> 상담</span>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>{m.text}</div>
            ))}
            {loading && <div className="chat-typing">입력 중...</div>}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <input
              className="chat-input"
              placeholder="메시지를 입력하세요..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              disabled={loading}
            />
            <button className="chat-send" onClick={send} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}

      {/* FAB 버튼 */}
      <button className="chat-fab" onClick={() => setOpen(o => !o)} aria-label="상담 챗봇 열기">
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="#C9A84C" strokeWidth="2.2" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        )}
      </button>
    </>
  )
}
