"use client"
import React from 'react'
import { ShotAnalysis } from '../../types'
import { useTranslations } from 'next-intl'

export default function ContextualAnalysisPanel({ analysis }: { analysis: ShotAnalysis }) {
  const t = useTranslations('Sidebar')
  
  if (!analysis.contextual_analysis) return null

  return (
    <div className="mb-8">
      <h3 className="text-[11px] text-gray-400 font-medium uppercase tracking-wider mb-3">
        {t('contextualAnalysisTitle')}
      </h3>
      <div className="relative p-5 bg-gradient-to-br from-white to-[#F9FAFB] rounded-2xl border border-gray-100 shadow-sm overflow-hidden group">
        {/* Decorative background element */}
        <div className="absolute -right-4 -top-4 w-24 h-24 bg-[#5B4FCF]/5 rounded-full blur-2xl group-hover:bg-[#5B4FCF]/10 transition-colors" />
        
        <div className="relative z-10">
          <p className="text-[14px] text-gray-800 leading-relaxed font-medium">
            {analysis.contextual_analysis}
          </p>
          
          <div className="mt-4 flex items-center gap-2">
            <div className="h-px flex-1 bg-gray-100" />
            <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest">
              AI Insight
            </span>
            <div className="h-px w-4 bg-gray-100" />
          </div>
        </div>
      </div>
    </div>
  )
}
