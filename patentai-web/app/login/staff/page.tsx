'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function StaffLogin() {
  const [staffId, setStaffId] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    alert('직원 로그인 버튼 클릭됨')
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0A0A16',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'Noto Sans KR', sans-serif",
      padding: '2rem',
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@300;400;500&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        .login-input {
          width: 100%;
          height: 48px;
          border: 1px solid #D8D2C8;
          border-radius: 0;
          padding: 0 14px;
          font-size: 0.9rem;
          outline: none;
          transition: border 0.2s;
        }
        .login-input:focus { border-color: #C9A84C; box-shadow: 0 0 0 1px #C9A84C; }
        .login-btn-submit {
          width: 100%;
          height: 50px;
          background: #111128;
          color: #C9A84C;
          border: 1px solid #111128;
          font-size: 0.9rem;
          font-weight: 700;
          cursor: pointer;
          margin-top: 0.8rem;
          transition: 0.2s;
          letter-spacing: 0.05em;
        }
        .login-btn-submit:hover { background: #C9A84C; color: #111128; border-color: #C9A84C; }
      `}</style>

      <Link href="/" style={{ textDecoration: 'none', marginBottom: '2rem' }}>
        <div style={{
          fontFamily: "'Noto Serif KR', serif",
          color: '#F0EDE6',
          letterSpacing: '0.22em',
          fontSize: '1.35rem',
          textAlign: 'center',
        }}>
          PATENT<em style={{ color: '#C9A84C', fontStyle: 'normal' }}>AI</em>
        </div>
      </Link>

      <div style={{
        background: '#F5F4F1',
        border: '1px solid rgba(201,168,76,0.35)',
        padding: '3rem',
        width: '100%',
        maxWidth: '480px',
        boxShadow: '0 22px 50px rgba(0,0,0,0.28)',
      }}>
        <div style={{ color: '#C9A84C', letterSpacing: '0.28em', fontSize: '0.72rem', fontWeight: 700, marginBottom: '1rem' }}>
          STAFF ACCESS
        </div>
        <div style={{ fontFamily: "'Noto Serif KR', serif", fontSize: '2.1rem', fontWeight: 300, color: '#111128', marginBottom: '0.6rem' }}>
          직원 로그인
        </div>
        <div style={{ color: '#666', lineHeight: 1.8, fontSize: '0.92rem', marginBottom: '2rem' }}>
          PatentAI 내부 직원 전용 페이지입니다.<br />
          상담 관리와 AI 분석 시스템에 접근할 수 있습니다.
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', color: '#222', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              직원 아이디
            </label>
            <input
              className="login-input"
              type="text"
              placeholder="직원 아이디 또는 이메일"
              value={staffId}
              onChange={e => setStaffId(e.target.value)}
              required
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#222', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.4rem' }}>
              비밀번호
            </label>
            <input
              className="login-input"
              type="password"
              placeholder="비밀번호"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <button className="login-btn-submit" type="submit">로그인</button>
        </form>

        <div style={{ marginTop: '1.5rem', paddingTop: '1.2rem', borderTop: '1px solid #DDD4C4', color: '#777', fontSize: '0.82rem', lineHeight: 1.7 }}>
          내부 직원만 접근 가능한 페이지입니다.<br />
          계정 문의는 관리자에게 문의하세요.{' '}
          <Link href="/login/client" style={{ color: '#C9A84C', textDecoration: 'none' }}>고객 로그인</Link>
        </div>
      </div>
    </div>
  )
}
