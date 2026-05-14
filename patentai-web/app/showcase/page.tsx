'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const slides = [
  {
    tag: 'AI-POWERED PATENT SYSTEM',
    title: '발명의 가치를\n권리로 만듭니다',
    sub: 'AI가 특허 출원의 전 과정을 자동화합니다',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #050510 0%, #0A0A20 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Nightview_of_the_Gwanghwamun_Square_2024.jpg',
  },
  {
    tag: '01 — 특허 상담 에이전트',
    title: '발명 내용을\nAI가 구조화합니다',
    sub: '문제점·해결수단·효과·구성요소를 단계적으로 정리',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #08081A 0%, #101025 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/c/cc/N_Seoul_Tower_%2813952097192%29.jpg',
  },
  {
    tag: '02 — 선행기술 조사',
    title: 'KIPRIS · USPTO · EPO\n전 세계 특허 DB 탐색',
    sub: '벡터 유사도 + 키워드 하이브리드 검색으로 정확도 극대화',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #050510 0%, #0D0D22 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/1/14/Seoul_Skyline_Night_2018.jpg',
  },
  {
    tag: '03 — 도면 자동 생성',
    title: '특허청 실무 수준\nSVG 도면을 자동 생성',
    sub: '블록도·흐름도·시퀀스·상태도 — 품질 점수 A등급',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #08081A 0%, #0A0A1E 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Nightview_of_the_Gwanghwamun_Square_2024.jpg',
  },
  {
    tag: '04 — 명세서 작성',
    title: 'sLLM 파인튜닝으로\n청구항을 자동 작성',
    sub: 'EXAONE 기반 특허 특화 모델 — 변리사 비용 40% 절감',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #050510 0%, #0D0820 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/c/cc/N_Seoul_Tower_%2813952097192%29.jpg',
  },
  {
    tag: 'PATENTAI — SKN25 3팀',
    title: '6인의 AI 전문가\n팀이 만들었습니다',
    sub: '권가영 · 김서현 · 김홍익 · 박범수 · 조은석 · 최현우',
    accent: '#C9A84C',
    bg: 'linear-gradient(135deg, #08081A 0%, #101020 100%)',
    img: 'https://upload.wikimedia.org/wikipedia/commons/1/14/Seoul_Skyline_Night_2018.jpg',
  },
]

export default function ShowcasePage() {
  const [current, setCurrent] = useState(0)
  const [progress, setProgress] = useState(0)
  const DURATION = 5000

  useEffect(() => {
    setProgress(0)
    const step = 50
    const inc = (step / DURATION) * 100
    const timer = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          setCurrent(c => (c + 1) % slides.length)
          return 0
        }
        return p + inc
      })
    }, step)
    return () => clearInterval(timer)
  }, [current])

  const s = slides[current]

  return (
    <div style={{
      width: '100vw', height: '100vh',
      background: s.bg,
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden', position: 'relative',
      fontFamily: "'Noto Sans KR', sans-serif",
      transition: 'background 0.8s ease',
    }}>
      {/* 배경 이미지 */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `url(${s.img})`,
        backgroundSize: 'cover', backgroundPosition: 'center',
        opacity: 0.08,
        transition: 'opacity 0.8s ease',
      }} />

      {/* 상단 바 */}
      <div style={{
        position: 'relative', zIndex: 10,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '2rem 3rem',
        borderBottom: '1px solid rgba(201,168,76,.12)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <svg width="32" height="32" viewBox="0 0 36 36" fill="none">
            <rect width="36" height="36" fill="#0A0A16"/>
            <rect x="1" y="1" width="34" height="34" stroke="#C9A84C" strokeWidth="1"/>
            <path d="M10 10 L10 26" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round"/>
            <path d="M10 10 L17 10 Q22 10 22 15 Q22 20 17 20 L10 20" stroke="#C9A84C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
            <circle cx="26" cy="22" r="1.5" fill="#C9A84C"/>
          </svg>
          <div>
            <div style={{ fontFamily: "'Noto Serif KR',serif", color: '#F0EDE6', fontSize: '0.9rem', letterSpacing: '.2em', fontWeight: 300 }}>
              PATENT<span style={{ color: '#C9A84C' }}>AI</span>
            </div>
            <div style={{ color: '#333355', fontSize: '0.55rem', letterSpacing: '.12em' }}>IP CONSULTATION</div>
          </div>
        </div>
        <div style={{ color: '#333355', fontSize: '0.7rem', letterSpacing: '.15em' }}>
          {String(current + 1).padStart(2, '0')} / {String(slides.length).padStart(2, '0')}
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div style={{
        flex: 1, position: 'relative', zIndex: 10,
        display: 'flex', alignItems: 'center',
        padding: '0 6rem',
      }}>
        <div style={{ maxWidth: 800 }}>
          <div style={{
            color: '#C9A84C', fontSize: '0.7rem', fontWeight: 700,
            letterSpacing: '.4em', marginBottom: '1.5rem',
            textTransform: 'uppercase',
          }}>
            {s.tag}
          </div>
          <h1 style={{
            fontFamily: "'Noto Serif KR',serif",
            fontSize: 'clamp(2.8rem, 5vw, 5rem)',
            fontWeight: 200, color: '#F0EDE6',
            lineHeight: 1.35, margin: '0 0 1.5rem',
            whiteSpace: 'pre-line',
            letterSpacing: '-.01em',
          }}>
            {s.title}
          </h1>
          <div style={{
            color: '#666688', fontSize: 'clamp(0.9rem, 1.5vw, 1.1rem)',
            lineHeight: 1.8, maxWidth: 560, fontWeight: 300,
          }}>
            {s.sub}
          </div>

          {current === 0 && (
            <Link href="/" style={{
              display: 'inline-block', marginTop: '2.5rem',
              padding: '1rem 2.8rem',
              border: '1px solid rgba(201,168,76,.5)',
              color: '#C9A84C', fontSize: '0.78rem',
              fontWeight: 500, letterSpacing: '.16em',
              textDecoration: 'none', transition: '.2s',
            }}>
              서비스 살펴보기 →
            </Link>
          )}
        </div>
      </div>

      {/* 하단 — 진행 바 + 슬라이드 도트 */}
      <div style={{
        position: 'relative', zIndex: 10,
        padding: '1.5rem 3rem 2.5rem',
      }}>
        {/* 진행 바 */}
        <div style={{ height: 1, background: 'rgba(255,255,255,.08)', marginBottom: '1.2rem', position: 'relative' }}>
          <div style={{
            position: 'absolute', left: 0, top: 0,
            height: '100%', background: '#C9A84C',
            width: `${((current / slides.length) + (progress / 100 / slides.length)) * 100}%`,
            transition: 'width .05s linear',
          }} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* 도트 */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {slides.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrent(i)}
                style={{
                  width: i === current ? 24 : 6,
                  height: 6, border: 'none', cursor: 'pointer',
                  background: i === current ? '#C9A84C' : 'rgba(255,255,255,.2)',
                  transition: 'all .3s',
                  padding: 0,
                }}
              />
            ))}
          </div>

          {/* 스킵 */}
          <Link href="/" style={{
            color: '#333355', fontSize: '0.7rem',
            letterSpacing: '.1em', textDecoration: 'none',
            transition: 'color .15s',
          }}
            onMouseEnter={e => (e.currentTarget.style.color = '#C9A84C')}
            onMouseLeave={e => (e.currentTarget.style.color = '#333355')}
          >
            ENTER SITE →
          </Link>
        </div>
      </div>
    </div>
  )
}
