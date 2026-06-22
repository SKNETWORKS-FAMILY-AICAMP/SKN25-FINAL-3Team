import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface Props {
  children: React.ReactNode
  redirectTo?: string
}

export default function ProtectedRoute({ children, redirectTo = '/login' }: Props) {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-400">
        로딩 중...
      </div>
    )
  }

  if (!user) {
    return <Navigate to={redirectTo} replace state={{ from: `${location.pathname}${location.search}` }} />
  }

  return <>{children}</>
}
