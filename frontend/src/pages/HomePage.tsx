import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="pt-[70px]">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-8 py-32 bg-gradient-to-b from-[#0f172a] to-slate-900">
        <h1 className="text-5xl font-bold leading-tight mb-6 max-w-3xl">
          AI로 특허 명세서를<br />
          <span className="text-sky-400">빠르게 작성하세요</span>
        </h1>
        <p className="text-slate-400 text-lg mb-10 max-w-xl leading-relaxed">
          발명가와 변리사를 위한 스마트 특허 문서 생성 서비스.<br />
          아이디어 입력만으로 명세서 초안을 빠르게 생성합니다.
        </p>
        <div className="flex gap-4">
          {user ? (
            <Link to="/dashboard" className="btn-primary text-base px-8 py-4">
              대시보드로 가기
            </Link>
          ) : (
            <>
              <Link to="/signup" className="btn-primary text-base px-8 py-4">
                지금 시작하기
              </Link>
              <Link
                to="/login"
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold text-base px-8 py-4 rounded-xl transition-colors border border-slate-700"
              >
                로그인
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-8 bg-slate-900">
        <h2 className="text-center text-3xl font-bold mb-16 text-white">주요 기능</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="card text-center">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-bold mb-3 text-sky-400">AI 자동 생성</h3>
            <p className="text-slate-400 leading-relaxed">
              발명 내용을 입력하면 특허 명세서 초안을 자동으로 생성합니다. 청구항, 도면, 명세서까지 한 번에.
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h3 className="text-xl font-bold mb-3 text-sky-400">선행기술 분석</h3>
            <p className="text-slate-400 leading-relaxed">
              멀티에이전트 파이프라인이 선행기술을 자동 검색하고 차별성을 분석합니다.
            </p>
          </div>
          <div className="card text-center">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-bold mb-3 text-sky-400">빠른 문서화</h3>
            <p className="text-slate-400 leading-relaxed">
              반복적인 문서 작업 시간을 획기적으로 단축합니다. 변리사와 협업도 간편합니다.
            </p>
          </div>
        </div>
      </section>

      {/* Pipeline stages */}
      <section className="py-24 px-8 bg-[#0f172a]">
        <h2 className="text-center text-3xl font-bold mb-4 text-white">AI 파이프라인</h2>
        <p className="text-center text-slate-400 mb-16">발명 설명 입력 → 멀티에이전트 처리 → 완성된 특허 문서</p>
        <div className="flex flex-wrap justify-center gap-4 max-w-4xl mx-auto">
          {['발명 분석', '선행기술 검색', '청구항 작성', '도면 생성', '명세서 작성', '품질 검토'].map(
            (stage, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="bg-sky-500/20 border border-sky-500/40 rounded-full px-5 py-2 text-sky-300 text-sm font-medium">
                  {stage}
                </div>
                {i < 5 && <span className="text-slate-600">→</span>}
              </div>
            )
          )}
        </div>
      </section>

      {/* CTA */}
      {!user && (
        <section className="py-20 px-8 text-center bg-slate-900">
          <h2 className="text-3xl font-bold mb-4">지금 바로 시작하세요</h2>
          <p className="text-slate-400 mb-8">무료로 특허 AI 서비스를 경험해보세요.</p>
          <Link to="/signup" className="btn-primary text-base px-10 py-4">
            무료로 시작하기
          </Link>
        </section>
      )}
    </div>
  )
}
