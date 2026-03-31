"use client"
import React, { useState, useEffect, useRef } from 'react'
import { useFilmStore } from '../../store/useFilmStore'
import { ErrorBoundary } from '../ErrorBoundary'
import SourcesPanel from './SourcesPanel'
import PaperCitationsPanel from './PaperCitationsPanel'
import ContextualAnalysisPanel from './ContextualAnalysisPanel'
import { useTranslations } from 'next-intl'

// Tabs enum
type TabType = 'ANALYSIS' | 'RESEARCH' | 'OVERVIEW' | 'INQUIRY'

// Standard debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])
  return debouncedValue
}

// Layout sub-components
const ShotHeader = ({ shot, analysis, t }: any) => (
  <div className="flex items-center gap-3 mb-6">
    <div className="h-2 w-2 rounded-full bg-[#5B4FCF] animate-pulse" />
    <span className="font-bold text-[15px] text-gray-900">
      {t('scene')} {shot?.shot_id || '-'}{analysis?.shot_scale ? ` · ${analysis.shot_scale}` : ''} {shot ? ` · ${shot.duration.toFixed(0)}秒` : ''}
    </span>
  </div>
)

const TechniqueChips = ({ analysis, t }: any) => {
  const chips = [
    analysis?.shot_scale,
    analysis?.camera_movement,
    analysis?.camera_angle,
    analysis?.depth_of_field,
    analysis?.lighting_scheme,
    analysis?.color_temperature
  ].filter(Boolean)

  if (chips.length === 0) return null

  return (
    <div className="mb-8">
      <h3 className="text-[11px] text-gray-400 font-medium uppercase tracking-wider mb-3">{t('cameraLighting')}</h3>
      <div className="flex flex-wrap gap-2">
        {chips.map((chip, idx) => (
          <span
            key={idx}
            className="bg-[#F3F4F6] text-[#4B5563] px-3 py-1.5 rounded-full text-[12px] font-medium border border-gray-100 shadow-sm"
          >
            {chip}
          </span>
        ))}
      </div>
    </div>
  )
}

const TheorySection = ({ analysis, t }: any) => {
  if (!analysis?.theoretical_connections?.length) return null
  return (
    <div className="mb-8">
      <h3 className="text-[11px] text-gray-400 font-medium uppercase tracking-wider mb-3">{t('theory')}</h3>
      {analysis.theoretical_connections.map((tItem: any, i: number) => (
        <div
          key={i}
          className="mb-4 p-5 bg-[#F9FAFB] rounded-xl border border-gray-100 shadow-sm transition-all hover:shadow-md"
        >
          <div className="font-bold text-[#5B4FCF] text-[15px] leading-tight mb-1">
            {tItem.theory_name_cn} · <span className="text-[13px] font-medium opacity-80">{tItem.theory_name_en}</span>
          </div>
          <div className="text-[12px] text-gray-500 mb-3 italic">
            {tItem.theorist_cn} ({tItem.year})
          </div>
          <div className="leading-relaxed text-[13.5px] text-gray-700">
            {tItem.description}
          </div>
        </div>
      ))}
    </div>
  )
}

const ChatInput = ({ t, onSend }: { t: any, onSend: (text: string) => void }) => {
  const [text, setText] = useState('')
  const handleSend = () => {
    if (text.trim()) {
      onSend(text)
      setText('')
    }
  }

  return (
    <div className="mt-auto border-t border-gray-100 bg-white p-4">
      <div className="flex gap-2 p-1.5 bg-[#F9FAFB] border border-gray-200 rounded-xl focus-within:ring-2 focus-within:ring-[#5B4FCF]/20 transition-all">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={t('askPlaceholder')}
          className="flex-1 bg-transparent border-none text-gray-900 px-3 py-2 text-[13px] focus:outline-none"
        />
        <button 
          onClick={handleSend}
          className="bg-[#5B4FCF] text-white px-5 py-2 rounded-lg text-xs font-bold hover:bg-[#4A3EBD] transition-colors shadow-lg shadow-[#5B4FCF]/20"
        >
          发送
        </button>
      </div>
    </div>
  )
}

const SkeletonUI = () => (
  <div className="animate-pulse space-y-6">
    <div className="h-6 bg-gray-100 rounded-lg w-1/2" />
    <div className="space-y-3">
      <div className="h-3 bg-gray-100 rounded w-1/4" />
      <div className="flex gap-2">
        <div className="h-8 bg-gray-100 rounded-full w-20" />
        <div className="h-8 bg-gray-100 rounded-full w-24" />
        <div className="h-8 bg-gray-100 rounded-full w-16" />
      </div>
    </div>
    <div className="space-y-3">
      <div className="h-3 bg-gray-100 rounded w-1/3" />
      <div className="h-40 bg-gray-100 rounded-2xl" />
    </div>
  </div>
)

interface AnalysisSidebarProps {
  sendMessage?: (data: any) => void
}

export default function AnalysisSidebar({ sendMessage }: AnalysisSidebarProps) {
  const rawCurrentShotId = useFilmStore(state => state.currentShotId)
  const shots = useFilmStore(state => state.shots)
  const analyses = useFilmStore(state => state.analyses)
  const filmContext = useFilmStore(state => state.filmContext)
  const chatMessages = useFilmStore(state => state.chatMessages)
  const addChatMessage = useFilmStore(state => state.addChatMessage)
  const t = useTranslations('Sidebar')

  const currentShotId = useDebounce(rawCurrentShotId, 100)
  const [displayedShotId, setDisplayedShotId] = useState(currentShotId)
  const [isFading, setIsFading] = useState(false)
  const [activeTab, setActiveTab] = useState<TabType>('ANALYSIS')
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (currentShotId !== displayedShotId) {
      setIsFading(true)
      const timer = setTimeout(() => {
        setDisplayedShotId(currentShotId)
        setIsFading(false)
      }, 150)
      return () => clearTimeout(timer)
    }
  }, [currentShotId, displayedShotId])

  useEffect(() => {
    if (activeTab === 'INQUIRY') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatMessages, activeTab])

  const handleSendChat = (text: string) => {
    if (!sendMessage) return

    // 1. Add user message locally
    const userMsg = {
      id: Math.random().toString(36).substring(7),
      role: 'user' as const,
      content: text,
      timestamp: Date.now(),
      shotId: displayedShotId || undefined
    }
    addChatMessage(userMsg)

    // 2. Send via socket
    sendMessage({
      event: 'chat_request',
      question: text,
      shot_id: displayedShotId
    })

    // 3. Switch to inquiry tab if not there
    if (activeTab !== 'INQUIRY') {
      setActiveTab('INQUIRY')
    }
  }

  const shot = shots.find(s => s.shot_id === displayedShotId)
  const analysis = analyses[displayedShotId as number]

  const TabButton = ({ type, label }: { type: TabType, label: string }) => (
    <button
      onClick={() => setActiveTab(type)}
      className={`px-4 py-3 text-[14px] font-bold transition-all border-b-2 relative ${activeTab === type
        ? 'text-[#5B4FCF] border-[#5B4FCF]'
        : 'text-gray-400 border-transparent hover:text-gray-600'
        }`}
    >
      {label}
    </button>
  )

  if (!displayedShotId) {
    return (
      <div className="w-[380px] border-l border-gray-100 bg-white flex flex-col items-center justify-center text-center p-10">
        <div className="w-16 h-16 rounded-full bg-[#F3F4F6] flex items-center justify-center mb-6">
          <svg className="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <p className="text-[15px] font-bold text-gray-900 mb-2">准备就绪</p>
        <p className="text-[13px] text-gray-400 leading-relaxed">播放视频或点击时间轴以调起<br />大模型拉片分析结果</p>
      </div>
    )
  }

  return (
    <div className="w-[380px] shrink-0 border-l border-gray-100 bg-white flex flex-col h-full shadow-2xl relative z-10">
      {/* Tab Header */}
      <div className="flex border-b border-gray-100 px-4 shrink-0 bg-white/80 backdrop-blur-md sticky top-0 overflow-x-auto hide-scrollbar">
        <TabButton type="ANALYSIS" label="镜头分析" />
        <TabButton type="RESEARCH" label="论文引用" />
        <TabButton type="OVERVIEW" label="全片概览" />
        <TabButton type="INQUIRY" label="追问" />
      </div>

      <div className={`flex-1 overflow-y-auto hide-scrollbar transition-all duration-200 ${isFading ? 'opacity-0 translate-y-2' : 'opacity-100 translate-y-0'}`}>
        <div className="p-6">
          {activeTab === 'ANALYSIS' && (
            analysis ? (
              <ErrorBoundary fallbackMessage="由于数据格式变更，该镜头渲染失败">
                <ShotHeader shot={shot} analysis={analysis} t={t} />
                <TechniqueChips analysis={analysis} t={t} />
                <ContextualAnalysisPanel analysis={analysis} />
                <TheorySection analysis={analysis} t={t} />
                <SourcesPanel analysis={analysis} />
              </ErrorBoundary>
            ) : (
              <SkeletonUI />
            )
          )}

          {activeTab === 'RESEARCH' && (
            <div className="p-6">
              <PaperCitationsPanel researchMap={filmContext?.research_map} />
            </div>
          )}

          {activeTab === 'OVERVIEW' && (
            filmContext ? (
              <div className="space-y-6">
                <div className="p-5 bg-[#5B4FCF] rounded-2xl text-white shadow-xl shadow-[#5B4FCF]/20 mb-8">
                  <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] opacity-70 mb-1">Film Analysis Report</h4>
                  <h2 className="text-xl font-black mb-1 leading-tight">{filmContext.film_title}</h2>
                  <p className="text-[13px] font-medium opacity-90">
                    {filmContext.director} · {filmContext.production_year} · {filmContext.country_of_production}
                  </p>
                </div>

                <div className="space-y-6">
                  <div>
                    <h3 className="text-[11px] text-gray-400 font-bold uppercase tracking-widest mb-3">视觉与叙事总结</h3>
                    <p className="text-[13.5px] text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-xl border border-gray-100">
                      {filmContext.summary}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    {[
                      { label: '政治互文', content: filmContext.political, icon: 'M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9' },
                      { label: '经济背景', content: filmContext.economic, icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
                      { label: '文化研究', content: filmContext.cultural, icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
                      { label: '性别与权力', content: filmContext.gender_sexuality, icon: 'M12 4.354l1.1 3.383h3.558l-2.877 2.09 1.1 3.383-2.881-2.09-2.881 2.09 1.1-3.383-2.877-2.09h3.558L12 4.354z' }
                    ].map((item, idx) => (
                      <div key={idx} className="p-4 rounded-xl border border-gray-100 hover:border-[#5B4FCF]/30 transition-colors group">
                        <div className="flex items-center gap-2 mb-2 text-[#5B4FCF]">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} /></svg>
                          <span className="text-[12px] font-bold">{item.label}</span>
                        </div>
                        <p className="text-[12.5px] text-gray-500 leading-relaxed group-hover:text-gray-700 transition-colors">
                          {item.content}
                        </p>
                      </div>
                    ))}
                  </div>

                  {filmContext.auteur_biography && (
                    <div className="p-5 bg-gradient-to-br from-[#5B4FCF]/5 to-[#F9FAFB] rounded-2xl border border-[#5B4FCF]/10">
                      <h3 className="text-[11px] text-[#5B4FCF] font-bold uppercase tracking-widest mb-3 flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                        作者性风格分析
                      </h3>
                      <p className="text-[13px] text-gray-700 leading-relaxed italic">
                        "{filmContext.auteur_biography}"
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-20 text-center animate-pulse">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6">
                  <div className="w-8 h-8 border-2 border-[#5B4FCF] border-t-transparent rounded-full animate-spin"></div>
                </div>
                <h4 className="font-bold text-gray-900 mb-2">生成全片宏观报告中</h4>
                <p className="text-xs text-gray-400 px-4">正在总结 镜头分析 里的视听语言与理论互文，即将输出深度研报...</p>
              </div>
            )
          )}

          {activeTab === 'INQUIRY' && (
            <div className="space-y-4">
              {chatMessages.length === 0 ? (
                <div className="h-full flex flex-col justify-center items-center py-20 opacity-40">
                  <svg className="w-10 h-10 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                  <p className="text-sm font-medium text-center">在这里追问大模型<br/>关于当前镜头或全片的深度见解</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {chatMessages.map((msg) => (
                    <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[90%] px-4 py-3 rounded-2xl text-[13.5px] leading-relaxed shadow-sm ${
                        msg.role === 'user' 
                          ? 'bg-[#5B4FCF] text-white rounded-tr-none' 
                          : 'bg-[#F3F4F6] text-gray-800 rounded-tl-none border border-gray-100'
                      }`}>
                        {msg.content}
                      </div>
                      <span className="text-[10px] text-gray-400 mt-1 px-1">
                        {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        {msg.shotId && ` · 基于第 ${msg.shotId} 镜`}
                      </span>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <ChatInput t={t} onSend={handleSendChat} />
    </div>
  )
}
