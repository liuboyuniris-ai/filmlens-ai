"use client"
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LanguageSwitcher() {
  const router = useRouter()
  const [isMounted, setIsMounted] = useState(false)
  const [isEn, setIsEn] = useState(false)
  
  useEffect(() => {
    setIsMounted(true)
    setIsEn(document.cookie.includes('NEXT_LOCALE=en-US'))
  }, [])
  
  const toggleLanguage = () => {
    const nextLocale = isEn ? 'zh-CN' : 'en-US'
    document.cookie = `NEXT_LOCALE=${nextLocale}; path=/; max-age=31536000` // 1 year TTL
    setIsEn(!isEn)
    router.refresh()
  }

  if (!isMounted) return null

  return (
    <button 
      onClick={toggleLanguage} 
      className="text-xs px-2.5 py-1 bg-[#1A1A1A] text-gray-400 border border-gray-800 rounded hover:bg-gray-800 hover:text-white transition-colors"
    >
      {isEn ? '中/EN' : 'EN/中'}
    </button>
  )
}
