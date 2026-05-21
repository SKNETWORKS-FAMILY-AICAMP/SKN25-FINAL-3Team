import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()

    if (!body.consultation_note?.trim() && !body.structured_invention) {
      return NextResponse.json({ error: '발명 내용을 입력해주세요.' }, { status: 400 })
    }

    const res = await fetch(`${BACKEND}/generate-drawings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(180_000), // 도면 생성은 최대 3분
    })

    if (!res.ok) {
      const err = await res.text()
      return NextResponse.json({ error: `백엔드 오류: ${err}` }, { status: res.status })
    }

    const data = await res.json()

    // svg_url이 상대경로(/drawing-files/...)면 백엔드 절대 URL로 변환
    if (data.figures) {
      data.figures = data.figures.map((fig: { svg_url?: string }) => ({
        ...fig,
        svg_url: fig.svg_url?.startsWith('/')
          ? `${BACKEND}${fig.svg_url}`
          : fig.svg_url,
      }))
    }

    // 참조부호 필터링 — IPC 코드, 날짜, 긴 문장 등 제거
    if (data.reference_numerals) {
      data.reference_numerals = data.reference_numerals.filter(
        (r: { number: string; label: string }) => {
          const label = r.label?.trim() || ''
          if (!label) return false
          if (label.length > 20) return false            // 너무 긴 텍스트
          if (/G0[0-9][A-Z]/.test(label)) return false  // IPC 코드 (G06F 등)
          if (/^\d{4}/.test(label)) return false         // 날짜로 시작
          if (/[()[\]]/.test(label)) return false        // 괄호 포함
          return true
        }
      )
    }

    return NextResponse.json(data)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '알 수 없는 오류'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
