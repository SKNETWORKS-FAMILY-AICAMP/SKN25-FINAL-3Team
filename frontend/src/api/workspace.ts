// src/api/workspace.ts
import { api } from './client'

// --- Types ---
export interface Project {
  id: number
  title: string
  created_at: string
  status: string
  has_claims: boolean
}

export interface InventionInput {
  problem_to_solve: string
  prior_art_problem: string
  core_tech: string
  expected_effect: string
}

export interface ConsultationState {
  ext_problem?: string
  ext_solution?: string
  ext_differentiation?: string
  ext_effect?: string
}

export interface ChatMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
}

export interface WorkstationData {
  project: Project
  invention_input: InventionInput
  consultation_state: ConsultationState
  chat_messages: ChatMessage[]
  prior_art_json: string
}

// --- API Functions ---
export const workspaceApi = {
  // 1. 워크스테이션 초기 데이터 불러오기 (GET)
  getWorkstation: (projectId: string) =>
    api.get<WorkstationData>(`/auth/workspace/workstation/${projectId}/`),

  // 2. 채팅 메시지 전송 (POST)
  sendMessage: (projectId: string, message: string) =>
    api.post<{ message: string, reply: string }>(`/auth/workspace/workstation/${projectId}/chat_api/`, { message }),

  // 3. 파일 업로드 (FormData 사용 필요)
  uploadFile: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    // api.post 대신 fetch를 직접 사용하거나, client.ts를 확장해야 할 수 있습니다. 
    // 임시로 fetch 기반 구현
    const token = localStorage.getItem('access_token')
    return fetch(`/auth/workspace/workstation/${projectId}/upload_api/`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    }).then(res => res.json())
  },

  // 4. 파이프라인 액션들 (POST)
  generateClaims: (projectId: string) =>
    api.post<{ message: string }>(`/auth/workspace/workstation/${projectId}/generate_claims_api/`, {}),

  generateDrawings: (projectId: string) =>
    api.post<{ message: string }>(`/auth/workspace/workstation/${projectId}/generate_drawings_api/`, {}),

  generateSpecification: (projectId: string) =>
    api.post<{ message: string }>(`/auth/workspace/workstation/${projectId}/generate_specification_api/`, {}),
}