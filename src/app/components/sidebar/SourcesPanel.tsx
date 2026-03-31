"use client"
import React from 'react'
import { ShotAnalysis, PaperSource, TheoryRef } from '../../types'
import { useTranslations } from 'next-intl'

const DATABASE_DISPLAY: Record<string, { label: string, region: string, color: string, badge: string }> = {
  "SemanticScholar": { "label": "Semantic Scholar", "region": "INTL", "color": "#1857B6", "badge": "S2" },
  "CrossRef": { "label": "CrossRef / DOI", "region": "INTL", "color": "#E18335", "badge": "DOI" },
  "CNKI": { "label": "中国知网 CNKI", "region": "CN", "color": "#DE2910", "badge": "知" },
  "JSTOR": { "label": "JSTOR", "region": "US", "color": "#2B5797", "badge": "J" },
  "GoogleScholar": { "label": "Google Scholar", "region": "INTL", "color": "#4285F4", "badge": "G" },
  "WanFang": { "label": "万方数据", "region": "CN", "color": "#C0392B", "badge": "万" },
  "VIP": { "label": "维普期刊", "region": "CN", "color": "#E74C3C", "badge": "维" },
  "ProQuest": { "label": "ProQuest", "region": "US", "color": "#003865", "badge": "PQ" },
  "PhilPapers": { "label": "PhilPapers", "region": "INTL", "color": "#5B4FCF", "badge": "PP" },
}

interface SourcesPanelProps {
  analysis: ShotAnalysis
}

const SourceItem = ({ source }: { source: PaperSource }) => {
  const display = DATABASE_DISPLAY[source.database] || { label: source.database, region: source.region, color: '#555', badge: 'DB' }
  const t = useTranslations('Sidebar')

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-start gap-3 p-3 bg-white hover:bg-[#F9FAFB] rounded-xl text-left transition-all border border-gray-100 shadow-sm hover:shadow-md group"
    >
      <div
        className="w-[20px] h-[15px] flex-shrink-0 rounded-[3px] text-[9px] font-bold flex items-center justify-center mt-0.5 text-white shadow-sm"
        style={{ backgroundColor: display.color }}
      >
        {display.badge}
      </div>

      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-gray-400 mb-0.5 flex justify-between items-center">
          <span>{display.label}</span>
          {source.is_open_access && (
            <span className="text-[9px] text-[#059669] bg-[#ECFDF5] px-1.5 py-0.5 rounded-sm border border-[#D1FAE5]">{t('freeFullText')}</span>
          )}
        </div>
        <div className="text-[13px] text-gray-800 font-bold leading-snug line-clamp-2 mb-1 group-hover:text-[#5B4FCF] transition-colors">
          {source.title}
        </div>
        <div className="text-[10px] text-gray-400 truncate font-medium">
          {source.author} · {source.year} {source.journal ? `· ${source.journal}` : ''}
        </div>
      </div>

      <svg className="w-3.5 h-3.5 text-gray-300 group-hover:text-[#5B4FCF] mt-1 flex-shrink-0 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
      </svg>
    </a>
  )
}

const SourceSkeleton = () => (
  <div className="animate-pulse flex flex-col gap-2">
    <div className="h-[72px] bg-gray-50 rounded-xl border border-gray-100"></div>
    <div className="h-[72px] bg-gray-50 rounded-xl border border-gray-100"></div>
    <div className="h-[72px] bg-gray-50 rounded-xl border border-gray-100"></div>
  </div>
)

export default function SourcesPanel({ analysis }: SourcesPanelProps) {
  const theories = analysis.theoretical_connections || []
  const t = useTranslations('Sidebar')
  if (theories.length === 0) return null

  // Check overall loading state
  const isAnyLoading = theories.some(t => !t.sources_loaded)
  const isAnyError = theories.some(t => t.sources_error)

  // Aggregate and deduplicate all sources
  const allSourcesMap = new Map<string, PaperSource>()
  theories.forEach(t => {
    (t.sources || []).forEach(s => {
      if (s.url && !allSourcesMap.has(s.url)) {
        allSourcesMap.set(s.url, s)
      }
    })
  })

  let allSources = Array.from(allSourcesMap.values())

  // Sort Open Access First -> Citation Count High -> Name Fallback
  allSources.sort((a, b) => {
    if (a.is_open_access !== b.is_open_access) {
      return a.is_open_access ? -1 : 1
    }
    return (b.citation_count || 0) - (a.citation_count || 0)
  })

  const intlSources = allSources.filter(s => s.region !== 'CN')
  const cnSources = allSources.filter(s => s.region === 'CN')

  return (
    <div className="mb-6">
      <div className="text-[11px] text-gray-500 uppercase tracking-widest mb-3 flex items-center justify-between">
        <span>{t('sourcesTitle')}</span>
        {isAnyLoading && (
          <svg className="w-3 h-3 text-gray-500 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4V2m0 20v-2m8-8h2M2 12h2m15.364 6.364l-1.414-1.414M5.05 5.05l1.414 1.414m12.728 0l-1.414 1.414M5.05 18.95l1.414-1.414" />
          </svg>
        )}
      </div>

      {isAnyError && !isAnyLoading && allSources.length === 0 && (
        <div className="text-xs text-red-500 bg-red-50 border border-red-100 p-3 rounded-lg mb-3">
          自动搜索失败。
          <br />
          理论检索遇到了网络错误。
        </div>
      )}

      {isAnyLoading && allSources.length === 0 ? (
        <SourceSkeleton />
      ) : (
        <div className="flex flex-col gap-2">
          {intlSources.map(s => <SourceItem key={s.url || s.title} source={s} />)}

          {cnSources.length > 0 && (
            <>
              {intlSources.length > 0 && (
                <div className="flex items-center my-2">
                  <div className="flex-1 h-px bg-gray-100"></div>
                  <div className="text-[10px] text-gray-300 px-3 font-bold uppercase tracking-widest">{t('chineseLiterature')}</div>
                  <div className="flex-1 h-px bg-gray-100"></div>
                </div>
              )}
              {cnSources.map(s => <SourceItem key={s.url || s.title} source={s} />)}
            </>
          )}
        </div>
      )}
    </div>
  )
}
