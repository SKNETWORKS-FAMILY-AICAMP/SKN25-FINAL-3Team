'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import ScrollReveal from '@/components/ScrollReveal'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'
import { useEffect, useRef, useState } from 'react'

function useCountUp(target: number, duration = 1400) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLElement>(null)
  const started = useRef(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !started.current) {
        started.current = true
        const start = performance.now()
        const tick = (now: number) => {
          const pct = Math.min((now - start) / duration, 1)
          const ease = 1 - Math.pow(1 - pct, 3)
          setCount(Math.round(ease * target))
          if (pct < 1) requestAnimationFrame(tick)
        }
        requestAnimationFrame(tick)
        obs.unobserve(el)
      }
    }, { threshold: 0.5 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [target, duration])

  return { count, ref }
}

function StatItem({ target, label, suffix = '' }: { target: number; label: string; suffix?: string }) {
  const { count, ref } = useCountUp(target)
  return (
    <div className="stat">
      <b ref={ref as React.RefObject<HTMLElement>}>{count}{suffix}</b>
      <p>{label}</p>
    </div>
  )
}

export default function Home() {
  const { lang } = useLang()
  const h = t.home

  return (
    <div className="site">
      <style>{`
.card { transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s !important; }
        .card:hover { transform: translateY(-3px) !important; box-shadow: 0 12px 32px rgba(0,0,0,.07) !important; }
        .step { transition: background .2s, transform .25s cubic-bezier(.22,1,.36,1) !important; }
        .step:hover { transform: translateY(-2px) !important; }
      `}</style>

      <Nav />

      <div className="hero home">
        <img className="hero-img img1"
          src="https://upload.wikimedia.org/wikipedia/commons/6/6c/Nightview_of_the_Gwanghwamun_Square_2024.jpg"
          alt="광화문 광장" />
        <img className="hero-img img2"
          src="https://upload.wikimedia.org/wikipedia/commons/c/cc/N_Seoul_Tower_%2813952097192%29.jpg"
          alt="N서울타워 야경" />
        <img className="hero-img img3"
          src="https://upload.wikimedia.org/wikipedia/commons/1/14/Seoul_Skyline_Night_2018.jpg"
          alt="롯데월드타워" />

        <div className="hero-content">
          <div className="tag">{tr(h.tag, lang)}</div>
          <h1>{tr(h.h1, lang).split('\n').map((l, i) => <span key={i}>{l}{i === 0 && <br />}</span>)}</h1>
          <div className="line"></div>
          <p>{tr(h.desc, lang).split('\n').map((l, i) => <span key={i}>{l}{i === 0 && <br />}</span>)}</p>
          <Link className="btn" href="/service">{tr(h.cta, lang)}</Link>
        </div>
      </div>

      {/* 카운터 애니메이션 통계 */}
      <div className="stats">
        <StatItem target={6}    label={tr(h.stat1, lang)} />
        <StatItem target={5}    label={tr(h.stat3, lang)} />
        <StatItem target={114}  label="FAQ 데이터베이스" />
        <StatItem target={2026} label="SKN25 3팀" />
      </div>

      {/* 서비스 카드 */}
      <div className="section">
        <ScrollReveal>
          <div className="sec-line"></div>
          <div className="sec-title">{tr(h.svcTitle, lang)}</div>
          <div className="sec-sub">{tr(h.svcSub, lang)}</div>
        </ScrollReveal>
        <div className="grid">
          <ScrollReveal delay={0}>
            <Link href="/service"><div className="card"><div className="num">01</div><h3>{tr(h.svc1h, lang)}</h3><p>{tr(h.svc1p, lang)}</p></div></Link>
          </ScrollReveal>
          <ScrollReveal delay={120}>
            <Link href="/service"><div className="card"><div className="num">02</div><h3>{tr(h.svc2h, lang)}</h3><p>{tr(h.svc2p, lang)}</p></div></Link>
          </ScrollReveal>
          <ScrollReveal delay={240}>
            <Link href="/service"><div className="card"><div className="num">03</div><h3>{tr(h.svc3h, lang)}</h3><p>{tr(h.svc3p, lang)}</p></div></Link>
          </ScrollReveal>
        </div>
      </div>

      {/* 기존 변리사 vs PatentAI 비교 */}
      <ScrollReveal>
      <div style={{ background: '#07071A', borderTop: '1px solid rgba(201,168,76,.12)', borderBottom: '1px solid rgba(201,168,76,.12)', padding: '5.5rem 6.5rem' }}>
        <style>{`
          .cmp-wrap { max-width: 1100px; margin: 0 auto; }
          .cmp-tag { color: #C9A84C; font-size: .62rem; font-weight: 700; letter-spacing: .4em; margin-bottom: 1.2rem; }
          .cmp-title { font-family: 'Noto Serif KR', serif; font-size: 2rem; font-weight: 200; color: #EDE8E0; margin-bottom: .6rem; line-height: 1.5; }
          .cmp-sub { color: #55556A; font-size: .88rem; margin-bottom: 3.5rem; }
          .cmp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: rgba(201,168,76,.1); }
          .cmp-col { padding: 0; }
          .cmp-col-head { padding: 1.2rem 2rem; display: flex; align-items: center; gap: .8rem; }
          .cmp-col-head-old { background: #0E0E22; }
          .cmp-col-head-new { background: rgba(201,168,76,.1); }
          .cmp-col-label { font-size: .72rem; font-weight: 700; letter-spacing: .12em; }
          .cmp-col-label-old { color: #44445A; }
          .cmp-col-label-new { color: #C9A84C; }
          .cmp-col-dot { width: 8px; height: 8px; border-radius: 50%; }
          .cmp-col-dot-old { background: #44445A; }
          .cmp-col-dot-new { background: #C9A84C; }
          .cmp-row { display: contents; }
          .cmp-cell { padding: 1.1rem 2rem; border-top: 1px solid rgba(255,255,255,.04); display: flex; align-items: flex-start; gap: .8rem; }
          .cmp-cell-old { background: #0A0A18; }
          .cmp-cell-new { background: rgba(201,168,76,.04); }
          .cmp-cell-icon { font-size: .9rem; flex-shrink: 0; margin-top: .1rem; }
          .cmp-cell-text { font-size: .86rem; line-height: 1.65; word-break: keep-all; }
          .cmp-cell-text-old { color: #44445A; }
          .cmp-cell-text-new { color: #B8A87A; }
          .cmp-cell-label { font-size: .6rem; font-weight: 700; letter-spacing: .12em; color: #333355; display: block; margin-bottom: .15rem; }
          .cmp-cell-label-new { color: #7A6A3A; }
          .cmp-bottom { margin-top: 2.5rem; display: flex; gap: 2.5rem; flex-wrap: wrap; }
          .cmp-stat { border-left: 2px solid rgba(201,168,76,.3); padding-left: 1.2rem; }
          .cmp-stat-num { font-family: 'Noto Serif KR', serif; font-size: 2rem; font-weight: 200; color: #C9A84C; letter-spacing: .04em; }
          .cmp-stat-label { font-size: .72rem; color: #44445A; margin-top: .2rem; letter-spacing: .06em; }
          @media(max-width:900px){ .cmp-grid { grid-template-columns: 1fr; } .cmp-wrap { padding: 0; } }
          @media(max-width:480px){ div[style*="5.5rem 6.5rem"] { padding: 3.5rem 1.4rem !important; } }
        `}</style>
        <div className="cmp-wrap">
          <div className="cmp-tag">WHY PATENTAI</div>
          <div className="cmp-title">기존 변리사무소와 무엇이 다른가요?</div>
          <div className="cmp-sub">PatentAI는 변리사를 대체하지 않습니다. 변리사가 더 잘할 수 있도록 AI가 초안의 전 과정을 자동화합니다.</div>

          <div className="cmp-grid">
            {/* 헤더 */}
            <div className="cmp-col-head cmp-col-head-old">
              <span className="cmp-col-dot cmp-col-dot-old" />
              <span className="cmp-col-label cmp-col-label-old">기존 변리사무소</span>
            </div>
            <div className="cmp-col-head cmp-col-head-new">
              <span className="cmp-col-dot cmp-col-dot-new" />
              <span className="cmp-col-label cmp-col-label-new">PATENTAI</span>
            </div>

            {[
              {
                label: '비용',
                old: '명세서 작성 단독 200–500만 원\n선행기술 조사 별도 50–100만 원',
                neu: '초안 자동화로 변리사 검토 시간 60–80% 단축\n전체 비용 대폭 절감',
              },
              {
                label: '처리 시간',
                old: '명세서 초안 작성 2–4주\n선행기술 조사 1–2주',
                neu: '명세서 초안 3–7분\n선행기술 조사 2–5분\n도면 자동 생성 30초',
              },
              {
                label: '접근성',
                old: '대면 미팅 또는 이메일·전화 필수\n영업시간(평일 9–18시)만 가능',
                neu: '24시간 365일 온라인 접근\n언어 제한 없음 (한/영/일/중)',
              },
              {
                label: '투명성',
                old: '진행 상황을 알기 어려움\n결과물만 전달받는 구조',
                neu: '단계별 AI 처리 결과 즉시 확인\n구조화 JSON·리포트 자동 생성',
              },
              {
                label: '도면 품질',
                old: '도면사 별도 의뢰 필요\n수작업으로 수정 반복',
                neu: '특허청 실무 기준 SVG 자동 생성\n품질 점수 자동 검증 (A/B/C/D 등급)',
              },
              {
                label: '선행기술 조사',
                old: 'KIPRIS 수동 키워드 검색\n조사 범위·누락 위험',
                neu: 'KIPRIS·USPTO·EPO 동시 벡터 검색\nRRF 하이브리드로 신규성 위험 사전 파악',
              },
            ].map((row, i) => (
              <div key={i} className="cmp-row">
                <div className="cmp-cell cmp-cell-old">
                  <span className="cmp-cell-icon" style={{ color: '#333355' }}>✕</span>
                  <div className="cmp-cell-text cmp-cell-text-old">
                    <span className="cmp-cell-label">{row.label}</span>
                    {row.old.split('\n').map((l, j) => <span key={j} style={{ display: 'block' }}>{l}</span>)}
                  </div>
                </div>
                <div className="cmp-cell cmp-cell-new">
                  <span className="cmp-cell-icon" style={{ color: '#C9A84C' }}>✓</span>
                  <div className="cmp-cell-text cmp-cell-text-new">
                    <span className="cmp-cell-label cmp-cell-label-new">{row.label}</span>
                    {row.neu.split('\n').map((l, j) => <span key={j} style={{ display: 'block' }}>{l}</span>)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="cmp-bottom">
            {[
              { num: '60–80%', label: '변리사 초안 작업 시간 단축' },
              { num: '30초', label: '특허 도면 자동 생성' },
              { num: '3개국', label: '특허 DB 동시 조사 (KR·US·EU)' },
              { num: '24 / 7', label: '언제나 접근 가능' },
            ].map(s => (
              <div key={s.label} className="cmp-stat">
                <div className="cmp-stat-num">{s.num}</div>
                <div className="cmp-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      </ScrollReveal>

      {/* 워크플로 */}
      <div className="section dark">
        <ScrollReveal>
          <div className="sec-line"></div>
          <div className="sec-title">{tr(h.flowTitle, lang)}</div>
          <div className="sec-sub">{tr(h.flowSub, lang)}</div>
        </ScrollReveal>
        <div className="workflow">
          {[h.step1, h.step2, h.step3, h.step4, h.step5].map((step, i) => (
            <ScrollReveal key={i} delay={i * 80}>
              <div className="step"><b>0{i + 1}</b><p>{tr(step, lang)}</p></div>
            </ScrollReveal>
          ))}
        </div>
      </div>


      <Footer />
    </div>
  )
}
