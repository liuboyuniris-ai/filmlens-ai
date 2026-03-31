"use client"
import React, { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useFilmStore } from '../../store/useFilmStore'
import { useAnalysisSocket } from '../../hooks/useAnalysisSocket'
import VideoPlayer from '../../components/player/VideoPlayer'
import ShotTimeline from '../../components/player/ShotTimeline'
import AnalysisSidebar from '../../components/sidebar/AnalysisSidebar'
import { ErrorBoundary } from '../../components/ErrorBoundary'
import { useTranslations } from 'next-intl'
import LanguageSwitcher from '../../components/LanguageSwitcher'

export default function AnalyzePage() {
  const [mounted, setMounted] = React.useState(false)

  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string

  // Instantiate WebSocket Connection directly mapping to store
  const { error, sendMessage } = useAnalysisSocket(jobId)

  const videoUrl = useFilmStore(state => state.videoUrl)
  const shots = useFilmStore(state => state.shots)
  const isAnalyzing = useFilmStore(state => state.isAnalyzing)
  const analyzedCount = useFilmStore(state => state.analyzedCount)

  const t = useTranslations('Analyze')

  // Diagnostics
  useEffect(() => {
    setMounted(true)
    console.log(`[AnalyzePage] Mounted. JobId: ${jobId}`)
    console.log(`[AnalyzePage] videoUrl: ${videoUrl ? (videoUrl.startsWith('blob:') ? 'Blob URL' : videoUrl) : 'NULL'}`)
    console.log(`[AnalyzePage] shots count: ${shots.length}`)
  }, [jobId, videoUrl, shots.length])

  if (!mounted) return null

  if (!videoUrl) {
    return (
      <div className="w-full h-screen bg-black flex flex-col items-center justify-center text-gray-400 gap-4">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#5B4FCF]"></div>
        <p>{t('pulling')}</p>
      </div>
    )
  }

  return (
    <div className="w-full h-screen bg-[#050505] text-white overflow-hidden flex flex-col font-sans">
      {/* 顶部控制台 */}
      <header className="h-[56px] border-b border-gray-800 flex justify-between items-center px-7 shrink-0 bg-[#000000] shadow-sm z-20">
        <div className="font-bold text-[17px] tracking-tight text-gray-100 flex items-center gap-3">
          <span className="text-[#5B4FCF]">{t('title')}</span>
          <span className="text-gray-700 font-normal">/</span>
          <span className="text-gray-300 font-medium text-[14px]">{t('workspace')}</span>

          {error && <span className="ml-3 px-2 py-0.5 text-[11px] bg-red-900/30 text-red-400 border border-red-800 rounded">Socket 警告: {error}</span>}
        </div>

        <div className="flex items-center gap-5 text-[13px] font-semibold tracking-wide">
          <LanguageSwitcher />

          {shots.length > 0 && (
            <div className="text-gray-400 bg-[#0F0F0F] px-4 py-1.5 rounded-md border border-gray-800 tabular-nums shadow-inner">
              {t('analyzed')} <span className="text-gray-100 px-1">{analyzedCount}</span> / <span className="text-gray-500 pl-1">{shots.length}</span> {t('shots')}
            </div>
          )}

          {isAnalyzing ? (
            <div className="flex items-center gap-3 text-[#7E74ED] bg-[#5B4FCF]/10 px-4 py-1.5 rounded-md border border-[#5B4FCF]/30 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#AFa9EC] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#7E74ED]"></span>
              </span>
              <span>{t('analyzing')}</span>
            </div>
          ) : shots.length > 0 ? (
            <div className="flex items-center gap-2.5 text-[#5DCAA5] bg-[#5DCAA5]/10 px-4 py-1.5 rounded-md border border-[#5DCAA5]/30">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
              <span>{t('completed')}</span>
            </div>
          ) : (
            <div className="flex items-center gap-2.5 text-[#E18335] bg-[#E18335]/10 px-4 py-1.5 rounded-md border border-[#E18335]/30">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#E18335] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#E18335]"></span>
              </span>
              <span>{t('detecting')}</span>
            </div>
          )}
        </div>
      </header>

      {/* 核心联动区域 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左盘：播放器与时间轴 - Added min-w-0 to prevent pushing sidebar off-screen */}
        <div className="flex-1 flex flex-col relative bg-[#020202] min-w-0">
          <div className="flex-1 flex items-center justify-center p-2 min-w-0">
            <ErrorBoundary fallbackMessage={t('errorBoundary')}>
              <VideoPlayer src={videoUrl} />
            </ErrorBoundary>
          </div>

          <div className="h-[56px] border-t border-gray-800 shrink-0 bg-black">
            {shots.length > 0 ? (
              <ShotTimeline />
            ) : (
              <div className="w-full h-full bg-[#050505] flex items-center justify-center text-xs text-gray-700 font-bold tracking-[0.2em] uppercase">
                Detecting Cinematic Cuts
              </div>
            )}
          </div>
        </div>

        {/* 右盘：实时推注分析面板 */}
        <AnalysisSidebar sendMessage={sendMessage} />
      </div>
    </div>
  )
}
