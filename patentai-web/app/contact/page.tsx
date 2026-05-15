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
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (touched[name]) validate({ ...form, [name]: value })
  }

  function handleBlur(e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    setTouched(prev => ({ ...prev, [e.target.name]: true }))
    validate(form)
  }

  function validate(f: typeof form) {
    const errs: Record<string, string> = {}
    const nameLabel = lang === 'en' ? 'Name' : lang === 'ja' ? 'お名前' : lang === 'zh' ? '姓名' : '성함'
    const emailLabel = lang === 'en' ? 'Email' : lang === 'ja' ? 'メール' : lang === 'zh' ? '邮箱' : '이메일'
    const msgLabel = lang === 'en' ? 'Message' : lang === 'ja' ? 'メッセージ' : lang === 'zh' ? '消息' : '내용'
    if (!f.name.trim()) errs.name = `${nameLabel}${lang === 'ko' ? '을' : ''} 입력해 주세요`
    if (!f.email.trim()) errs.email = `${emailLabel}${lang === 'ko' ? '을' : ''} 입력해 주세요`
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) errs.email = lang === 'en' ? 'Invalid email format' : lang === 'ja' ? 'メール形式が正しくありません' : lang === 'zh' ? '邮箱格式不正确' : '올바른 이메일 형식이 아닙니다'
    if (!f.message.trim()) errs.message = `${msgLabel}${lang === 'ko' ? '을' : ''} 입력해 주세요`
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setTouched({ name: true, email: true, phone: true, message: true })
    if (validate(form)) setSubmitted(true)
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
        .form-error { color: #c0392b; font-size: 0.76rem; margin-top: 0.2rem; }
        .form-input.err, .form-textarea.err { border-color: #c0392b; }
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
            <div className="contact-info-item"><div><strong>ADDRESS</strong><span style={{ whiteSpace: 'pre-line' }}>{tr(t.footer.address, lang)}</span></div></div>
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
              <form onSubmit={handleSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">{tr(c.name, lang)} *</label>
                    <input className={`form-input${errors.name && touched.name ? ' err' : ''}`} name="name" placeholder="홍길동" value={form.name} onChange={handleChange} onBlur={handleBlur} />
                    {errors.name && touched.name && <div className="form-error">{errors.name}</div>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">{tr(c.phone, lang)}</label>
                    <input className="form-input" name="phone" placeholder="010-0000-0000" value={form.phone} onChange={handleChange} onBlur={handleBlur} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.email, lang)} *</label>
                  <input className={`form-input${errors.email && touched.email ? ' err' : ''}`} type="email" name="email" placeholder="example@email.com" value={form.email} onChange={handleChange} onBlur={handleBlur} />
                  {errors.email && touched.email && <div className="form-error">{errors.email}</div>}
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.type, lang)}</label>
                  <select className="form-select" name="category" value={form.category} onChange={handleChange}>
                    <option value="">{lang === 'en' ? 'Select...' : lang === 'ja' ? '選択...' : lang === 'zh' ? '请选择...' : '선택하세요'}</option>
                    <option value="consultation">{lang === 'en' ? 'Patent Consultation' : lang === 'ja' ? '特許相談' : lang === 'zh' ? '专利咨询' : '특허 상담'}</option>
                    <option value="priorart">{lang === 'en' ? 'Prior Art Search' : lang === 'ja' ? '先行技術調査' : lang === 'zh' ? '现有技术检索' : '선행기술 조사'}</option>
                    <option value="spec">{lang === 'en' ? 'Specification Writing' : lang === 'ja' ? '明細書作成' : lang === 'zh' ? '说明书撰写' : '명세서 작성'}</option>
                    <option value="drawing">{lang === 'en' ? 'Drawing Generation' : lang === 'ja' ? '図面生成' : lang === 'zh' ? '附图生成' : '도면 생성'}</option>
                    <option value="other">{lang === 'en' ? 'Other' : lang === 'ja' ? 'その他' : lang === 'zh' ? '其他' : '기타'}</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">{tr(c.msg, lang)} *</label>
                  <textarea className={`form-textarea${errors.message && touched.message ? ' err' : ''}`} name="message" value={form.message} onChange={handleChange} onBlur={handleBlur} />
                  {errors.message && touched.message && <div className="form-error">{errors.message}</div>}
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
