import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

const SYSTEM = `당신은 PatentAI의 특허 상담 전문 AI 어시스턴트입니다.
변리사 수준의 전문 지식을 바탕으로 특허 출원, 선행기술 조사, 명세서 작성, 도면 생성에 관해 안내합니다.

규칙:
- 항상 전문적이고 친절하게 답변합니다.
- 특허법 조문이나 근거가 있으면 함께 안내합니다.
- 법적 판단이 필요한 복잡한 사안은 전문 변리사 상담을 권장합니다.
- 답변은 간결하고 명확하게, 200자 이내로 유지합니다.
- 상담 신청이 필요한 경우 "/contact 페이지"를 안내합니다.
- 한국어로 답변합니다.`

export async function POST(req: NextRequest) {
  try {
    const { messages } = await req.json()
    const response = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      max_tokens: 400,
      temperature: 0.4,
      messages: [
        { role: 'system', content: SYSTEM },
        ...messages.slice(-6),
      ],
    })
    return NextResponse.json({ text: response.choices[0].message.content })
  } catch (e) {
    return NextResponse.json({ text: '일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.' }, { status: 500 })
  }
}
