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
  signup: (data: SignupPayload) =>
    api.post<AuthTokens>('/auth/api/auth/signup/', data),

  login: (username: string, password: string) =>
    api.post<AuthTokens>('/auth/api/auth/login/', { username, password }),

  logout: (refresh: string) =>
    api.post<{ message: string }>('/auth/api/auth/logout/', { refresh }),

  me: () =>
    api.get<{ user: User }>('/auth/api/auth/me/'),

  updateProfile: (data: { name?: string; email?: string }) =>
    api.patch<{ user: User }>('/auth/api/auth/me/', data),
}
