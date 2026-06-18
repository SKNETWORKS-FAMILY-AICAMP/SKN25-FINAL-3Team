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
  // 1. 회원가입: /auth/accounts/signup/ 으로 요청
  signup: (data: SignupPayload) =>
    api.post<AuthTokens>('/auth/accounts/signup/', data),

  // 2. 로그인: /auth/accounts/login/ 으로 요청
  login: (username: string, password: string) =>
    api.post<AuthTokens>('/auth/accounts/login/', { username, password }),

  // 3. 로그아웃: /auth/accounts/logout/ 으로 요청
  logout: (refresh: string) =>
    api.post<{ message: string }>('/auth/accounts/logout/', { refresh }),

  // 4. 내 정보 조회 및 수정 (필요시 백엔드 주소에 맞게 조정 가능)
  me: () =>
    api.get<{ user: User }>('/auth/accounts/me/'),

  updateProfile: (data: { name?: string; email?: string }) =>
    api.patch<{ user: User }>('/auth/accounts/me/', data),
}