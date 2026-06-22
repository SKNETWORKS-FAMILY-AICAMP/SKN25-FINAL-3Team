import { getAuthHeader, resolveAuthUrl } from './client'

export interface ClaimReviewInput {
  claim_no: number
  is_dependent: boolean
  cited_claim_no: number[]
  category: '방법' | '시스템' | 'CRM'
  content: string
}

export interface RejectionDetail {
  claims: number[]
  reason_text: string
}

export interface ExaminerResult {
  is_approved: boolean
  rejections: RejectionDetail[]
  revision_count: number
}

export interface ClaimReviewEvent {
  step: 'start' | 'examination' | 'rewrite' | 'done' | 'error'
  phase?: 'initial' | 'reexamination'
  message?: string
  examiner?: ExaminerResult
  claims?: ClaimReviewInput[]
  approved?: boolean
  was_rewritten?: boolean
  original_claims?: ClaimReviewInput[]
  final_claims?: ClaimReviewInput[]
}

export async function reviewClaimsStream(
  claimText: string,
  onEvent: (event: ClaimReviewEvent) => void,
) {
  const response = await fetch(resolveAuthUrl('/auth/workspace/review_claims_api/'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({ claim_text: claimText }),
  })

  if (response.status === 401) throw new Error('로그인 후 청구항 심사를 이용해 주세요.')
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || '청구항 심사 요청에 실패했습니다.')
  }
  if (!response.body) throw new Error('심사 결과 스트림을 열 수 없습니다.')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.trim()) onEvent(JSON.parse(line) as ClaimReviewEvent)
    }
    if (done) break
  }

  if (buffer.trim()) onEvent(JSON.parse(buffer) as ClaimReviewEvent)
}
