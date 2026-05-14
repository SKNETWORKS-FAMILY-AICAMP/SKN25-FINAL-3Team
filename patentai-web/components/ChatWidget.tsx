'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

type Message = {
  role: 'user' | 'bot'
  text: string
  links?: { label: string; href: string; external?: boolean }[]
}

const GREET = '안녕하세요! PatentAI 상담 도우미입니다.\n특허 관련 궁금한 점을 자유롭게 물어보세요.'

// ── 키워드 → 응답 + 링크 매핑 ───────────────────────────────
const KEYWORD_MAP: {
  keywords: string[]
  text: string
  links: { label: string; href: string; external?: boolean }[]
}[] = [
  {
    keywords: ['선행기술', '선행 기술', '유사특허', '유사 특허', '신규성', '진보성', 'kipris', 'KIPRIS', '특허 검색', '특허검색'],
    text: '선행기술 조사는 발명의 신규성·진보성을 확인하는 핵심 단계입니다.\nKIPRIS에서 무료로 검색하거나 PatentAI의 자동 조사 서비스를 이용할 수 있어요.',
    links: [
      { label: 'KIPRIS 특허 검색', href: 'https://www.kipris.or.kr', external: true },
      { label: 'Google Patents', href: 'https://patents.google.com', external: true },
      { label: 'PatentAI 서비스 소개', href: '/service' },
    ],
  },
  {
    keywords: ['도면', '블록도', '흐름도', '순서도', 'SVG', 'PNG', '도면 생성', '도면생성'],
    text: '특허 도면은 명세서의 핵심입니다.\nPatentAI 도면 에이전트는 텍스트 입력만으로 블록도·흐름도·시퀀스 다이어그램을 자동 생성해 드립니다.',
    links: [
      { label: 'PatentAI 서비스 소개', href: '/service' },
      { label: '특허청 도면 작성 가이드', href: 'https://www.kipo.go.kr', external: true },
    ],
  },
  {
    keywords: ['청구항', '청구 항', '명세서', '독립항', '종속항', '권리범위', '출원서'],
    text: '청구항은 특허의 권리범위를 정의하는 가장 중요한 부분입니다.\nPatentAI가 발명 내용을 분석하여 독립항·종속항 초안을 자동 작성해 드립니다.',
    links: [
      { label: 'PatentAI 명세서 작성 서비스', href: '/service' },
      { label: '특허로 온라인 출원', href: 'https://www.patent.go.kr', external: true },
    ],
  },
  {
    keywords: ['상담', '문의', '신청', '연락', '전화', '이메일', '어떻게 시작'],
    text: '상담 신청 페이지에서 발명 내용을 남겨주시면\n영업일 기준 1–2일 내 담당자가 연락드립니다.',
    links: [
      { label: '상담 신청하기', href: '/contact' },
    ],
  },
  {
    keywords: ['서비스', '기능', '무엇을', '뭘', '어떤', '제공', '할 수 있'],
    text: 'PatentAI는 다음 서비스를 제공합니다:\n① 특허 상담 에이전트\n② 선행기술 조사\n③ 명세서 작성\n④ 도면 자동 생성\n⑤ 심사 대응',
    links: [
      { label: '서비스 전체 보기', href: '/service' },
    ],
  },
  {
    keywords: ['팀', '구성원', '담당자', '누가', '개발자', '만든'],
    text: 'PatentAI는 SKN25 3팀이 개발한 AI 기반 지식재산 상담 시스템입니다.\n팀 구성원 소개 페이지에서 더 자세히 확인하세요.',
    links: [
      { label: '구성원 소개', href: '/team' },
    ],
  },
  {
    keywords: ['뉴스', '소식', '최신', '동향', 'IPC', 'CPC', '특허청', 'WIPO', 'KIPO'],
    text: '특허·IP 관련 최신 뉴스와 자료를 소식/자료 페이지에서 확인하세요.',
    links: [
      { label: '소식/자료 보기', href: '/news' },
      { label: '특허청 공식 사이트', href: 'https://www.kipo.go.kr', external: true },
    ],
  },
  {
    keywords: ['로그인', '회원', '계정', '비밀번호', '가입'],
    text: '고객 로그인과 직원 로그인 페이지를 이용해 주세요.',
    links: [
      { label: '고객 로그인', href: '/login/client' },
      { label: '직원 로그인', href: '/login/staff' },
    ],
  },
  {
    keywords: ['비용', '가격', '요금', '얼마', '무료'],
    text: '현재 PatentAI는 SKN25 프로젝트로 운영 중입니다.\n상담 신청 후 자세한 안내를 받아보실 수 있어요.',
    links: [
      { label: '상담 신청하기', href: '/contact' },
    ],
  },
]

function detectKeywords(text: string): typeof KEYWORD_MAP[0] | null {
  const lower = text.toLowerCase()
  for (const item of KEYWORD_MAP) {
    if (item.keywords.some(k => lower.includes(k.toLowerCase()))) {
      return item
    }
  }
  return null
}

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
    const newMessages = [...messages, { role: 'user' as const, text }]
    setMessages(newMessages)
    setLoading(true)

    // 키워드 감지 우선 — 페이지 링크 안내
    const matched = detectKeywords(text)
    if (matched) {
      await new Promise(r => setTimeout(r, 400))
      setMessages(prev => [...prev, {
        role: 'bot',
        text: matched.text,
        links: matched.links,
      }])
    } else {
      // 키워드 없으면 실제 GPT-4o-mini 호출
      try {
        const apiMessages = newMessages
          .filter(m => m.role === 'user' || m.role === 'bot')
          .map(m => ({ role: m.role === 'bot' ? 'assistant' : 'user', content: m.text }))

        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: apiMessages }),
        })
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'bot', text: data.text }])
      } catch {
        setMessages(prev => [...prev, {
          role: 'bot',
          text: '일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
          links: [{ label: '상담 신청하기', href: '/contact' }],
        }])
      }
    }
    setLoading(false)
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
        .chat-panel {
          position: fixed; bottom: 6rem; right: 2rem;
          width: 370px; height: 560px;
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
          border: 1.5px solid rgba(201,168,76,0.5); flex-shrink: 0;
        }
        .chat-header-name { color: #F0EDE6; font-size: 0.9rem; font-weight: 700; }
        .chat-header-name em { color: #C9A84C; font-style: normal; }
        .chat-header-status { color: #7777A0; font-size: 0.72rem; display: flex; align-items: center; gap: 0.3rem; margin-top: 1px; }
        .chat-header-status::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #4ade80; display: inline-block; }
        .chat-close { background: none; border: none; color: #666; font-size: 1.3rem; cursor: pointer; padding: 0; margin-left: auto; }
        .chat-close:hover { color: #C9A84C; }
        .chat-messages {
          flex: 1; overflow-y: auto; padding: 1rem 0.9rem;
          display: flex; flex-direction: column; gap: 1rem; background: #F8F7F5;
        }
        .chat-row { display: flex; align-items: flex-end; gap: 0.5rem; }
        .chat-row.user { flex-direction: row-reverse; }
        .chat-name { font-size: 0.72rem; font-weight: 600; margin-bottom: 3px; color: #888; }
        .chat-row.bot .chat-name { color: #C9A84C; }
        .chat-bubble-wrap { display: flex; flex-direction: column; max-width: 80%; }
        .chat-row.user .chat-bubble-wrap { align-items: flex-end; }
        .chat-bubble {
          padding: 0.65rem 0.95rem; font-size: 0.875rem;
          line-height: 1.65; white-space: pre-wrap;
        }
        .chat-bubble.bot {
          background: #fff; border: 1px solid #E8E4DC; color: #2a2a2a;
          border-radius: 0 12px 12px 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }
        .chat-bubble.user {
          background: #111128; color: #F0EDE6; border-radius: 12px 12px 0 12px;
        }
        .chat-links { display: flex; flex-direction: column; gap: 0.4rem; margin-top: 0.5rem; }
        .chat-link-btn {
          display: inline-flex; align-items: center; gap: 0.4rem;
          padding: 0.4rem 0.85rem; font-size: 0.78rem; font-weight: 600;
          border: 1px solid #C9A84C; color: #C9A84C; background: none;
          cursor: pointer; text-decoration: none; transition: 0.15s;
          border-radius: 20px; width: fit-content;
        }
        .chat-link-btn:hover { background: #C9A84C; color: #111128; }
        .typing-dots {
          background: #fff; border: 1px solid #E8E4DC;
          border-radius: 0 12px 12px 12px;
          padding: 0.65rem 1rem; display: flex; gap: 4px; align-items: center;
        }
        .typing-dots span {
          width: 6px; height: 6px; border-radius: 50%;
          background: #C9A84C; animation: bounce 1.2s infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
          0%,60%,100% { transform: translateY(0); opacity: 0.5; }
          30% { transform: translateY(-5px); opacity: 1; }
        }
        .chat-input-row { display: flex; border-top: 1px solid #E8E4DC; background: #fff; align-items: center; padding: 0 0.3rem; }
        .chat-input { flex: 1; border: none; padding: 0.9rem 0.7rem; font-size: 0.875rem; outline: none; background: transparent; font-family: inherit; }
        .chat-send { background: none; border: none; padding: 0 0.8rem; cursor: pointer; color: #C9A84C; font-size: 1.1rem; transition: color 0.15s; }
        .chat-send:hover { color: #111128; }
        .chat-send:disabled { color: #ddd; cursor: default; }
        @media (max-width: 480px) {
          .chat-panel { width: calc(100vw - 2rem); right: 1rem; bottom: 5rem; }
          .chat-fab { bottom: 1rem; right: 1rem; }
        }
      `}</style>

      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-header-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F0EDE6" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                <circle cx="12" cy="16" r="1.5" fill="#C9A84C" stroke="none"/>
              </svg>
            </div>
            <div style={{ flex: 1 }}>
              <div className="chat-header-name">PATENT<em>AI</em> 어시스턴트</div>
              <div className="chat-header-status">온라인 · 특허 상담 AI</div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-row ${m.role}`}>
                {m.role === 'bot' && <BotAvatar />}
                {m.role === 'user' && <UserAvatar />}
                <div className="chat-bubble-wrap">
                  <div className="chat-name">{m.role === 'bot' ? 'PatentAI' : '나'}</div>
                  <div className={`chat-bubble ${m.role}`}>{m.text}</div>
                  {m.links && m.links.length > 0 && (
                    <div className="chat-links">
                      {m.links.map(link => (
                        link.external
                          ? <a key={link.href} className="chat-link-btn" href={link.href} target="_blank" rel="noopener noreferrer">→ {link.label}</a>
                          : <Link key={link.href} className="chat-link-btn" href={link.href}>→ {link.label}</Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-row bot">
                <BotAvatar />
                <div className="typing-dots"><span/><span/><span/></div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <input
              className="chat-input"
              placeholder="예: 선행기술 조사가 뭔가요?"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              disabled={loading}
            />
            <button className="chat-send" onClick={send} disabled={loading || !input.trim()}>➤</button>
          </div>
        </div>
      )}

      <button className="chat-fab" onClick={() => setOpen(o => !o)} aria-label="상담 챗봇 열기">
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="#C9A84C" strokeWidth="2.2" strokeLinecap="round" width="26" height="26">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="26" height="26">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        )}
      </button>
    </>
  )
}
