import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(req: NextRequest) {
  try {
    const { consultation_note } = await req.json()

    if (!consultation_note?.trim()) {
      return NextResponse.json({ error: '발명 내용을 입력해주세요.' }, { status: 400 })
    }

    const res = await fetch(`${BACKEND}/generate-claims`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ consultation_note }),
      signal: AbortSignal.timeout(120_000), // 2분 타임아웃
    })

    if (!res.ok) {
      const err = await res.text()
      return NextResponse.json({ error: `백엔드 오류: ${err}` }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '알 수 없는 오류'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
