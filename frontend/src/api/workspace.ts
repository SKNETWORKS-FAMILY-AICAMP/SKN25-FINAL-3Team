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
  // 1-1. 환영 메시지 및 초기 상담 상태 업데이트 (POST)
  welcomeApi: (projectId: string) =>
    api.post<{ status: string, ai_message?: string, extracted_data: ConsultationState }>(`/auth/workspace/workstation/${projectId}/welcome_api/`, {}),

  // 2. 채팅 메시지 전송 (POST)
  sendMessage: (projectId: string, message: string) =>
    api.post<{ status: string, ai_message: string, extracted_data: ConsultationState }>(
      `/auth/workspace/workstation/${projectId}/chat_api/`, 
      { message }
    ),

    generateDrawings: (projectId: string) =>
    api.post<{ status: string; message: string; drawings: any[] }>(
      `/auth/workspace/workstation/${projectId}/generate_drawings_api/`,
      {}
    ),

    getReport: (projectId: string) =>
    api.get<any>(`/auth/workspace/workstation/${projectId}/report/`)
      .then(res => res.data ? res.data : res), 

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
  // generateClaims: (projectId: string) =>
  //   api.post<{ message: string }>(`/auth/workspace/workstation/${projectId}/generate_claims_api/`, {}),

  generateSpecification: (projectId: string) =>
    api.post<{ status: string; message: string; markdown: string; details: any }>(
      `/auth/workspace/workstation/${projectId}/generate_specification_api/`,{}
    ),

  generateClaimsStream: async (projectId: string, onMessage: (data: any) => void) => {
    const token = localStorage.getItem('access_token')
    
    const response = await fetch(`/auth/workspace/workstation/${projectId}/generate_claims_api/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
  

    if (!response.body) throw new Error("스트리밍을 지원하지 않는 브라우저입니다.")

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = '' // 데이터가 중간에 끊겨서 올 경우를 대비한 버퍼

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // 마지막 줄은 불완전할 수 있으므로 다시 버퍼에 넣음
      buffer = lines.pop() || '' 

      for (const line of lines) {
        if (line.trim()) {
          try {
            const parsedData = JSON.parse(line)
            onMessage(parsedData) // 프론트엔드 UI로 데이터 전달
          } catch (e) {
            console.error("JSON 파싱 에러:", line)
          }
        }
      }
    }
  },
  generateSpecStream: async (projectId: string, onMessage: (data: any) => void) => {
    const token = localStorage.getItem('access_token')
    
    const response = await fetch(`/auth/workspace/workstation/${projectId}/generate_specification_api/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.body) throw new Error("스트리밍을 지원하지 않는 브라우저입니다.")

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = '' 

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' 

      for (const line of lines) {
        if (line.trim()) {
          try {
            const parsedData = JSON.parse(line)
            onMessage(parsedData)
          } catch (e) {
            console.error("JSON 파싱 에러:", line)
          }
        }
      }
    }
  },
  // 5. 청구항 저장 (AI가 만들어준 초안 저장)
  saveClaims: (projectId: string, claims: any[]) =>
    api.post<{ status: string }>(`/auth/workspace/workstation/${projectId}/save_claims_api/`, { claims }),

  // 6. 청구항 조회 (수정 모달용)
  getClaims: (projectId: string) =>
    api.get<{ status: string, claims: any[] }>(`/auth/workspace/workstation/${projectId}/manage_claims_api/`),

  // 7. 청구항 수정 (수정 모달에서 저장)
  updateClaims: (projectId: string, claims: any[]) =>
    api.post<{ status: string }>(`/auth/workspace/workstation/${projectId}/manage_claims_api/`, { claims }),
}