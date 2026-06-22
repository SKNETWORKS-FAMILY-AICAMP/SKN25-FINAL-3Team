'use client'

import { createContext, useContext, useState, ReactNode } from 'react'
import { Lang } from '@/lib/i18n'

type LangContextType = { lang: Lang; setLang: (l: Lang) => void }

const LangContext = createContext<LangContextType>({ lang: 'ko', setLang: () => {} })

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('ko')
  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>
}

export function useLang() {
  return useContext(LangContext)
}
