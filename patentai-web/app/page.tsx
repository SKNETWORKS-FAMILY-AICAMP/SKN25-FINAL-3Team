'use client'

import Link from 'next/link'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function Home() {
  const { lang } = useLang()
  const h = t.home

  return (
    <div className="site">
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

      <div className="stats">
        <div className="stat"><b>1,240+</b><p>{tr(h.stat1, lang)}</p></div>
        <div className="stat"><b>98.2%</b><p>{tr(h.stat2, lang)}</p></div>
        <div className="stat"><b>12</b><p>{tr(h.stat3, lang)}</p></div>
        <div className="stat"><b>542+</b><p>{tr(h.stat4, lang)}</p></div>
      </div>

      <div className="section">
        <div className="sec-line"></div>
        <div className="sec-title">{tr(h.svcTitle, lang)}</div>
        <div className="sec-sub">{tr(h.svcSub, lang)}</div>
        <div className="grid">
          <Link href="/service"><div className="card"><div className="num">01</div><h3>{tr(h.svc1h, lang)}</h3><p>{tr(h.svc1p, lang)}</p></div></Link>
          <Link href="/service"><div className="card"><div className="num">02</div><h3>{tr(h.svc2h, lang)}</h3><p>{tr(h.svc2p, lang)}</p></div></Link>
          <Link href="/service"><div className="card"><div className="num">03</div><h3>{tr(h.svc3h, lang)}</h3><p>{tr(h.svc3p, lang)}</p></div></Link>
        </div>
      </div>

      <div className="section dark">
        <div className="sec-line"></div>
        <div className="sec-title">{tr(h.flowTitle, lang)}</div>
        <div className="sec-sub">{tr(h.flowSub, lang)}</div>
        <div className="workflow">
          <div className="step"><b>01</b><p>{tr(h.step1, lang)}</p></div>
          <div className="step"><b>02</b><p>{tr(h.step2, lang)}</p></div>
          <div className="step"><b>03</b><p>{tr(h.step3, lang)}</p></div>
          <div className="step"><b>04</b><p>{tr(h.step4, lang)}</p></div>
          <div className="step"><b>05</b><p>{tr(h.step5, lang)}</p></div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
