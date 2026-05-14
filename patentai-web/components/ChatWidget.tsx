'use client'

import { useState, useRef, useEffect } from 'react'

type Message = { role: 'user' | 'bot'; text: string }

const GREET = '안녕하세요! PatentAI 상담 도우미입니다.\n발명 내용이나 특허 관련 궁금한 점을 자유롭게 말씀해 주세요.'

function BotAvatar() {
  return (
    <div style={{
      width: 36, height: 36, borderRadius: '50%',
      background: 'linear-gradient(135deg, #111128, #C9A84C)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0, boxShadow: '0 2px 8px rgba(0,0,0,0.18)',
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#F0EDE6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        <circle cx="12" cy="16" r="1.5" fill="#C9A84C" stroke="none"/>
      </svg>
    </div>
  )
}

function UserAvatar() {
  return (
    <div style={{
      width: 36, height: 36, borderRadius: '50%',
      background: '#E8E4DC',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      flexShrink: 0,
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#666" strokeWidth="1.8" strokeLinecap="round">
        <circle cx="12" cy="8" r="4"/>
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
      </svg>
    </div>
  )
}

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
          position: fixed; bottom: 2rem; right: 2rem;
          width: 58px; height: 58px;
          background: #111128; border: 2px solid #C9A84C; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          cursor: pointer; z-index: 9999;
          box-shadow: 0 8px 24px rgba(0,0,0,0.3);
          transition: transform 0.2s, background 0.2s;
        }
        .chat-fab:hover { background: #C9A84C; transform: scale(1.08); }
        .chat-fab svg { width: 26px; height: 26px; }

        .chat-panel {
          position: fixed; bottom: 6rem; right: 2rem;
          width: 370px; height: 540px;
          background: #fff; border: 1px solid #E8E4DC;
          box-shadow: 0 24px 60px rgba(0,0,0,0.18);
          display: flex; flex-direction: column;
          z-index: 9998; animation: slideUp 0.22s ease;
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .chat-header {
          background: #111128; padding: 0.85rem 1.2rem;
          display: flex; align-items: center; gap: 0.75rem;
          border-bottom: 2px solid #C9A84C;
        }
        .chat-header-avatar {
          width: 38px; height: 38px; border-radius: 50%;
          background: linear-gradient(135deg, #1a1a3e, #C9A84C);
          display: flex; align-items: center; justify-content: center;
          border: 1.5px solid rgba(201,168,76,0.5);
          flex-shrink: 0;
        }
        .chat-header-info { flex: 1; }
        .chat-header-name { color: #F0EDE6; font-size: 0.9rem; font-weight: 700; letter-spacing: 0.03em; }
        .chat-header-name em { color: #C9A84C; font-style: normal; }
        .chat-header-status { color: #7777A0; font-size: 0.72rem; display: flex; align-items: center; gap: 0.3rem; margin-top: 1px; }
        .chat-header-status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #4ade80; display: inline-block; }
        .chat-close { background: none; border: none; color: #666; font-size: 1.3rem; cursor: pointer; padding: 0; transition: color 0.15s; }
        .chat-close:hover { color: #C9A84C; }

        .chat-messages {
          flex: 1; overflow-y: auto; padding: 1rem 0.9rem;
          display: flex; flex-direction: column; gap: 1rem;
          background: #F8F7F5;
        }

        .chat-row { display: flex; align-items: flex-end; gap: 0.5rem; }
        .chat-row.user { flex-direction: row-reverse; }

        .chat-name { font-size: 0.72rem; font-weight: 600; margin-bottom: 3px; color: #888; }
        .chat-row.bot .chat-name { color: #C9A84C; }

        .chat-bubble-wrap { display: flex; flex-direction: column; max-width: 78%; }
        .chat-row.user .chat-bubble-wrap { align-items: flex-end; }

        .chat-bubble {
          padding: 0.65rem 0.95rem;
          font-size: 0.875rem; line-height: 1.65; white-space: pre-wrap;
        }
        .chat-bubble.bot {
          background: #fff; border: 1px solid #E8E4DC; color: #2a2a2a;
          border-radius: 0 12px 12px 12px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .chat-bubble.user {
          background: #111128; color: #F0EDE6;
          border-radius: 12px 12px 0 12px;
        }

        .chat-typing {
          display: flex; align-items: flex-end; gap: 0.5rem;
        }
        .typing-dots {
          background: #fff; border: 1px solid #E8E4DC;
          border-radius: 0 12px 12px 12px;
          padding: 0.65rem 1rem;
          display: flex; gap: 4px; align-items: center;
        }
        .typing-dots span {
          width: 6px; height: 6px; border-radius: 50%;
          background: #C9A84C; animation: bounce 1.2s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
          30% { transform: translateY(-5px); opacity: 1; }
        }

        .chat-input-row {
          display: flex; border-top: 1px solid #E8E4DC; background: #fff;
          align-items: center; padding: 0 0.3rem;
        }
        .chat-input {
          flex: 1; border: none; padding: 0.9rem 0.7rem;
          font-size: 0.875rem; outline: none; background: transparent; font-family: inherit;
        }
        .chat-send {
          background: none; border: none; padding: 0 0.8rem;
          cursor: pointer; color: #C9A84C; font-size: 1.1rem; transition: color 0.15s;
        }
        .chat-send:hover { color: #111128; }
        .chat-send:disabled { color: #ddd; cursor: default; }

        @media (max-width: 480px) {
          .chat-panel { width: calc(100vw - 2rem); right: 1rem; bottom: 5rem; }
          .chat-fab { bottom: 1rem; right: 1rem; }
        }
      `}</style>

      {open && (
        <div className="chat-panel">
          {/* 헤더 */}
          <div className="chat-header">
            <div className="chat-header-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F0EDE6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                <circle cx="12" cy="16" r="1.5" fill="#C9A84C" stroke="none"/>
              </svg>
            </div>
            <div className="chat-header-info">
              <div className="chat-header-name">PATENT<em>AI</em> 어시스턴트</div>
              <div className="chat-header-status">온라인 · 특허 상담 AI</div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          {/* 메시지 */}
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-row ${m.role}`}>
                {m.role === 'bot' && <BotAvatar />}
                {m.role === 'user' && <UserAvatar />}
                <div className="chat-bubble-wrap">
                  <div className="chat-name">
                    {m.role === 'bot' ? 'PatentAI' : '나'}
                  </div>
                  <div className={`chat-bubble ${m.role}`}>{m.text}</div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-typing">
                <BotAvatar />
                <div className="typing-dots">
                  <span/><span/><span/>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력 */}
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

      {/* FAB */}
      <button className="chat-fab" onClick={() => setOpen(o => !o)} aria-label="상담 챗봇 열기">
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="#C9A84C" strokeWidth="2.2" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
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
