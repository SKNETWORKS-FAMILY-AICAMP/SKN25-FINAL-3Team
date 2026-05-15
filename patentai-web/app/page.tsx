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
        .review-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 1.4rem; }
        .review-card {
          background: white; border: 1px solid #E8E4DC; padding: 2rem;
          transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s, border-color .25s;
        }
        .review-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(0,0,0,.08); border-color: rgba(201,168,76,.4); }
        .review-stars { color: #C9A84C; font-size: 1rem; margin-bottom: 0.8rem; letter-spacing: 2px; }
        .review-text { color: #444; font-size: 0.9rem; line-height: 1.85; margin-bottom: 1.2rem; font-style: italic; word-break: keep-all; }
        .review-author { display: flex; align-items: center; gap: 0.75rem; }
        .review-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg,#111128,#252548); display: flex; align-items: center; justify-content: center; color: #C9A84C; font-family: 'Noto Serif KR',serif; font-size: 0.9rem; flex-shrink: 0; border: 1px solid rgba(201,168,76,.25); }
        .review-name { font-weight: 700; font-size: 0.88rem; color: #111128; }
        .review-role { font-size: 0.75rem; color: #999; margin-top: 2px; letter-spacing: .04em; }
        .card { transition: transform .25s cubic-bezier(.22,1,.36,1), box-shadow .25s !important; }
        .card:hover { transform: translateY(-3px) !important; box-shadow: 0 12px 32px rgba(0,0,0,.07) !important; }
        .step { transition: background .2s, transform .25s cubic-bezier(.22,1,.36,1) !important; }
        .step:hover { transform: translateY(-2px) !important; }
        @media(max-width:900px){ .review-grid { grid-template-columns: 1fr; } }
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

      {/* 고객 후기 */}
      <div className="section">
        <ScrollReveal>
          <div className="sec-line"></div>
          <div className="sec-title">고객 후기</div>
          <div className="sec-sub">PatentAI를 이용한 발명자·기업의 실제 경험입니다.</div>
        </ScrollReveal>
        <div className="review-grid">
          {[
            { initial:'K', name:'K 스타트업 대표', role:'AI 의료기기 분야', text:'"기술은 있었지만 특허 명세서 작성이 막막했는데, PatentAI로 3일 만에 초안을 완성했습니다. 변리사 검토 비용도 절반으로 줄었어요."' },
            { initial:'박', name:'박○○ 연구원', role:'반도체 소재 분야', text:'"선행기술 조사에 2주씩 걸렸는데 PatentAI로 하루 만에 유사 특허 리포트를 받았습니다. 신규성 위험을 미리 파악해 출원 전략을 수정할 수 있었어요."' },
            { initial:'L', name:'L 제조기업 IP팀', role:'기계/제조 분야', text:'"도면 에이전트로 블록도와 흐름도를 자동 생성하니 도면사 의뢰 비용이 없어졌습니다. 특허청 수준의 품질이 나와서 놀랐어요."' },
          ].map((r, i) => (
            <ScrollReveal key={r.name} delay={i * 100}>
              <div className="review-card">
                <div className="review-stars">★★★★★</div>
                <div className="review-text">{r.text}</div>
                <div className="review-author">
                  <div className="review-avatar">{r.initial}</div>
                  <div>
                    <div className="review-name">{r.name}</div>
                    <div className="review-role">{r.role}</div>
                  </div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  )
}
