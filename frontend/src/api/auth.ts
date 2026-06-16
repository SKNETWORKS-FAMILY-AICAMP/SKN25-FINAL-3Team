import { api } from './client'

export interface User {
  id: number
  username: string
  name: string
  email: string
  gender?: string
  age?: number
  is_login: boolean
}

export interface AuthTokens {
  access: string
  refresh: string
  user: User
  message: string
}

export interface SignupPayload {
  username: string
  name: string
  password: string
  password2: string
  gender?: string
  age?: number
}

export const authApi = {
  // 수정: 장고의 urls.py에 정의된 정확한 경로인 '/accounts/signup/' 사용
  signup: (data: SignupPayload) =>
    api.post<AuthTokens>('/accounts/signup/', data),

  login: (username: string, password: string) =>
    api.post<AuthTokens>('/accounts/login/', { username, password }),

  logout: (refresh: string) =>
    api.post<{ message: string }>('/accounts/logout/', { refresh }),

  // 주의: 현재 장고 urls.py에는 내 정보 조회(/me/)나 프로필 수정 API가 개통되어 있지 않습니다.
  // 백엔드에 해당 기능을 추가하거나, 프론트에서 마이페이지(/workspace/mypage/) 렌더링을 활용해야 합니다.
  // me: () => api.get<{ user: User }>('/accounts/me/'),
  // updateProfile: (data: { name?: string; email?: string }) => api.patch<{ user: User }>('/accounts/me/', data),
}
