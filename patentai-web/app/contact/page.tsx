'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

export default function ContactPage() {
  const { lang } = useLang()
  const c = t.contact
  const [form, setForm] = useState({ name: '', email: '', phone: '', category: '', message: '' })
  const [submitted, setSubmitted] = useState(false)

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  return (
    <div className="site">
      <style>{`
        .contact-grid { display: grid; grid-template-columns: 1fr 1.6fr; gap: 4rem; align-items: start; }
        .contact-info-card { background: #111128; padding: 2.5rem; color: #F0EDE6; }
        .contact-info-title { font-family: 'Noto Serif KR', serif; font-size: 1.4rem; font-weight: 300; margin-bottom: 0.5rem; }
        .contact-info-line { width: 36px; height: 2px; background: #C9A84C; margin: 1rem 0 1.5rem; }
        .contact-info-item { display: flex; gap: 0.8rem; margin-bottom: 1.2rem; font-size: 0.88rem; line-height: 1.7; color: #B8B8CC; }
        .contact-info-item strong { color: #C9A84C; font-size: 0.75rem; letter-spacing: 0.1em; display: block; margin-bottom: 0.2rem; }
        .contact-hours { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(201,168,76,0.2); font-size: 0.82rem; color: #7777A0; line-height: 1.8; white-space: pre-line; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .form-group { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 1rem; }
        .form-label { font-size: 0.82rem; font-weight: 600; color: #333; }
        .form-input, .form-select, .form-textarea { width: 100%; border: 1px solid #D8D2C8; padding: 0.75rem 1rem; font-size: 0.88rem; outline: none; font-family: inherit; transition: border 0.2s; background: white; }
        .form-input:focus, .form-select:focus, .form-textarea:focus { border-color: #C9A84C; box-shadow: 0 0 0 1px #C9A84C; }
        .form-textarea { resize: vertical; min-height: 140px; }
        .form-submit { width: 100%; height: 52px; background: #111128; color: #C9A84C; border: 1px solid #111128; font-size: 0.92rem; font-weight: 700; cursor: pointer; letter-spacing: 0.08em; transition: 0.2s; margin-top: 0.5rem; }
        .form-submit:hover { background: #C9A84C; color: #111128; }
        .success-box { background: #f0fdf4; border: 1px solid #86efac; padding: 2rem; text-align: center; color: #166534; }
        @media (max-width: 900px) { .contact-grid { grid-template-columns: 1fr; gap: 2rem; } .form-row { grid-template-columns: 1fr; } }
      `}</style>

      <Nav />
      <div className="hero">
        <div className="tag">{tr(c.tag, lang)}</div>
        <h1>{tr(c.h1, lang)}</h1>
        <p>{tr(c.desc, lang)}</p>
      </div>

      <div className="section">
        <div className="contact-grid">
          <div className="contact-info-card">
            <div className="contact-info-title">{tr(c.h1, lang)}</div>
            <div className="contact-info-line" />
            <div className="contact-info-item"><div><strong>ADDRESS</strong>서울특별시 강남구 테헤란로</div></div>
            <div className="contact-info-item"><div><strong>PHONE</strong>02-0000-0000</div></div>
            <div className="contact-info-item"><div><strong>EMAIL</strong>contact@patentai.kr</div></div>
            <div className="contact-info-item"><div><strong>KAKAO</strong>@PatentAI</div></div>
            <div className="contact-hours">
              <strong style={{ color: '#C9A84C', fontSize: '0.72rem', letterSpacing: '0.1em' }}>HOURS</strong>{'\n'}
              {tr(t.footer.hours, lang)}{'\n\n'}
              <span style={{ color: '#555577' }}>{tr(t.footer.emergency, lang)}</span>
            </div>
          </div>

          <div>
            {submitted ? (
              <div className="success-box">
                <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>✅</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.5rem' }}>{tr(c.successTitle, lang)}</div>
                <div style={{ fontSize: '0.9rem' }}>{tr(c.successDesc, lang)}</div>
              </div>
            ) : (
              <form onSubmit={e => { e.preventDefault(); setSubmitted(true) }}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">{tr(c.name, lang)} *</label>
                    <input className="form-input" name="name" placeholder="홍길동" value={form.name} onChange={handleChange} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label">{tr(c.phone, lang)} *</label>
                    <input className="form-input" name="phone" placeholder="010-0000-0000" value={form.phone} onChange={handleChange} required />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.email, lang)} *</label>
                  <input className="form-input" type="email" name="email" placeholder="example@email.com" value={form.email} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.type, lang)}</label>
                  <select className="form-select" name="category" value={form.category} onChange={handleChange}>
                    <option value=""></option>
                    <option>특허 상담</option>
                    <option>선행기술 조사</option>
                    <option>명세서 작성</option>
                    <option>도면 생성</option>
                    <option>기타</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.msg, lang)} *</label>
                  <textarea className="form-textarea" name="message" value={form.message} onChange={handleChange} required />
                </div>
                <button className="form-submit" type="submit">{tr(c.submit, lang)}</button>
              </form>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
