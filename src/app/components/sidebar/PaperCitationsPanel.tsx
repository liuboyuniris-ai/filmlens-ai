"use client"
import React from 'react'
import { FilmResearchMap, ResearchPaper } from '../../types'
import { useTranslations } from 'next-intl'

interface PaperCitationsPanelProps {
  researchMap?: FilmResearchMap
}

export default function PaperCitationsPanel({ researchMap }: PaperCitationsPanelProps) {
  const t = useTranslations('Sidebar')

  const categories = researchMap?.categories || []

  if (categories.length === 0) {
    return (
      <div className="py-20 text-center px-6">
        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
        </div>
        <h4 className="font-bold text-gray-900 mb-2">暂无深度学术讨论汇总</h4>
        <p className="text-[13px] text-gray-400 leading-relaxed">
          未能从 Google Scholar 或 Semantic Scholar 检索到该影片的特定深度研究摘要。你可以尝试在“全片概览”中查看宏观背景，或在“追问”中咨询更多信息。
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8 pb-12">
      <div className="p-5 bg-gradient-to-br from-[#5B4FCF] to-[#7C3AED] rounded-2xl text-white shadow-xl shadow-[#5B4FCF]/20 mb-8">
        <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] opacity-70 mb-1">Global Research Map</h4>
        <h2 className="text-xl font-black mb-1 leading-tight">{t('researchMap')}</h2>
        <p className="text-[12px] opacity-80 leading-relaxed mt-2">
          基于大模型对海量学术论文摘要的深度学习，自动识别本片在学术界最受关注的讨论维度。
        </p>
      </div>

      {categories.map((category, idx) => (
        <div key={idx} className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-4 w-1 bg-[#5B4FCF] rounded-full" />
            <h3 className="text-[15px] font-bold text-gray-900">{category.category_name}</h3>
          </div>
          
          <p className="text-[12px] text-gray-500 leading-relaxed px-4">
            {category.description}
          </p>

          <div className="space-y-4 pl-4">
            {category.papers.map((paper, pIdx) => (
              <div 
                key={pIdx} 
                className="p-5 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all group"
              >
                <div className="flex justify-between items-start gap-4 mb-3">
                  <h4 className="text-[14px] font-bold text-gray-800 leading-tight group-hover:text-[#5B4FCF] transition-colors">
                    {paper.title}
                  </h4>
                  <a 
                    href={paper.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="shrink-0 p-2 bg-gray-50 rounded-lg hover:bg-[#5B4FCF]/10 text-gray-400 hover:text-[#5B4FCF] transition-all"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                  </a>
                </div>

                <div className="text-[11px] text-gray-400 mb-4 font-medium italic">
                  {paper.author} ({paper.year})
                </div>

                <div className="bg-[#F9FAFB] rounded-lg p-4 border-l-2 border-[#5B4FCF]/30">
                  <div className="text-[11px] text-[#5B4FCF] font-bold uppercase mb-2 flex items-center gap-1.5">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
                    {t('excerpt')}
                  </div>
                  <p className={`text-[12.5px] leading-relaxed text-gray-600 ${paper.language === 'en' ? 'italic font-serif' : ''}`}>
                    {paper.excerpt}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
