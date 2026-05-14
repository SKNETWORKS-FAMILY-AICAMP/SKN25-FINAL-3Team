import type { Metadata } from 'next'
import './globals.css'
import ChatWidget from '@/components/ChatWidget'
import CookieBanner from '@/components/CookieBanner'
import { LangProvider } from '@/contexts/LangContext'

export const metadata: Metadata = {
  title: 'PatentAI - AI 기반 지식재산 상담 시스템',
  description: '발명 상담부터 선행기술 조사, 명세서 작성, 도면 생성까지 특허 출원 전 과정을 AI로 자동화합니다.',
  keywords: ['특허', '특허 출원', '선행기술 조사', '명세서 작성', '도면 생성', 'AI 특허', '지식재산', '변리사', 'PatentAI'],
  authors: [{ name: 'PatentAI' }],
  openGraph: {
    title: 'PatentAI - AI 기반 지식재산 상담 시스템',
    description: '발명 상담부터 특허 명세서 작성, 도면 생성까지 AI가 자동화합니다.',
    type: 'website',
    locale: 'ko_KR',
    siteName: 'PatentAI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PatentAI - AI 기반 지식재산 상담 시스템',
    description: 'AI로 특허 출원 전 과정을 자동화하는 지식재산 상담 서비스',
  },
  robots: { index: true, follow: true },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <LangProvider>
          {children}
          <ChatWidget />
          <CookieBanner />
        </LangProvider>
      </body>
    </html>
  )
}
