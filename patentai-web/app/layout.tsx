import type { Metadata } from 'next'
import './globals.css'
import ChatWidget from '@/components/ChatWidget'
import { LangProvider } from '@/contexts/LangContext'

export const metadata: Metadata = {
  title: 'PatentAI - 지식재산 상담 시스템',
  description: 'AI 기반 특허 출원 서비스',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <LangProvider>
          {children}
          <ChatWidget />
        </LangProvider>
      </body>
    </html>
  )
}
