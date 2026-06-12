import { api } from './client'

export interface PatentRun {
  run_id: string
  status: 'running' | 'completed' | 'failed' | 'wait_user'
  user_input: string
  current_agent?: string
  completed_agents: string[]
  errors: string[]
  master_decision?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

export interface RunResult {
  run_id: string
  state: Record<string, unknown>
  decision: Record<string, unknown>
}

export const pipelineApi = {
  run: (user_input: string, route?: string[]) =>
    api.post<RunResult>('/api/pipeline/run', { user_input, route }),

  continue: (state: Record<string, unknown>, user_input?: string, route?: string[]) =>
    api.post<RunResult>('/api/pipeline/continue', { state, user_input, route }),

  getRun: (run_id: string) =>
    api.get<PatentRun>(`/api/runs/${run_id}`),
}

// 로컬 스토리지에서 내 프로젝트 목록 관리
export interface StoredProject {
  run_id: string
  title: string
  created_at: string
  status: string
}

const STORAGE_KEY = 'patent_projects'

export const projectStore = {
  list(): StoredProject[] {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]')
    } catch {
      return []
    }
  },

  add(project: StoredProject) {
    const projects = projectStore.list()
    projectStore._save([project, ...projects])
  },

  updateStatus(run_id: string, status: string) {
    const projects = projectStore.list().map(p =>
      p.run_id === run_id ? { ...p, status } : p
    )
    projectStore._save(projects)
  },

  remove(run_id: string) {
    projectStore._save(projectStore.list().filter(p => p.run_id !== run_id))
  },

  _save(projects: StoredProject[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(projects))
  },
}
