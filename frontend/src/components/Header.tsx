import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-[70px] bg-[#0f172a]/90 backdrop-blur border-b border-slate-800 flex items-center justify-between px-8">
      <Link to="/" className="text-sky-400 font-bold text-xl">
        PatentAI
      </Link>

      <nav className="flex items-center gap-6 text-sm">
        <a href="#" className="text-slate-400 hover:text-white transition-colors">서비스 소개</a>
        <a href="#" className="text-slate-400 hover:text-white transition-colors">기능</a>
        <a href="#" className="text-slate-400 hover:text-white transition-colors">문의</a>

        {user ? (
          <>
            <Link to="/dashboard" className="text-sky-400 font-bold hover:text-sky-300 transition-colors">
              대시보드
            </Link>
            <Link to="/mypage" className="text-slate-300 hover:text-white transition-colors">
              마이페이지
            </Link>
            <button
              onClick={handleLogout}
              className="border border-slate-600 text-white px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
            >
              로그아웃
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="border border-sky-500 text-sky-400 px-4 py-2 rounded-lg hover:bg-sky-500/10 transition-colors"
            >
              로그인
            </Link>
            <Link
              to="/signup"
              className="bg-sky-500 text-white px-4 py-2 rounded-lg hover:bg-sky-600 transition-colors"
            >
              회원가입
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}
