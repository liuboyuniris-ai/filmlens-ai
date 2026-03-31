"use client"
import React, { useEffect, useRef, useState } from 'react'
import { useFilmStore } from '../../store/useFilmStore'
import { Shot } from '../../types'
import { useVirtualizer } from '@tanstack/react-virtual'

const Thumbnail = React.memo(({ 
  shot, 
  isCurrent, 
  isAnalyzed, 
  isAnalyzing,
  onClick 
}: { 
  shot: Shot, 
  isCurrent: boolean, 
  isAnalyzed: boolean, 
  isAnalyzing: boolean,
  onClick: (startTime: number) => void 
}) => {
  const [imgLoaded, setImgLoaded] = useState(false)

  return (
    <div 
      onClick={() => onClick(shot.start_time)}
      className={`relative flex-shrink-0 w-[80px] h-[56px] cursor-pointer transition-colors box-border ${
        isCurrent ? 'border-2 border-[#5B4FCF] z-10 scale-[1.05] shadow-lg rounded-[1px]' : 'border-0'
      }`}
    >
      {/* Thumbnail LQIP Blur Effect */}
      {isAnalyzed || isAnalyzing ? (
        <div className="w-full h-full relative overflow-hidden bg-gray-900">
          <img 
            src={shot.keyframe_url} 
            alt={`Scene ${shot.shot_id}`}
            onLoad={() => setImgLoaded(true)}
            className={`w-full h-full object-cover transition-all duration-200 ease-in-out ${
              imgLoaded ? 'opacity-100 blur-none' : 'opacity-60 blur-md scale-110'
            }`}
            loading="lazy" 
          />
        </div>
      ) : (
        <div className="w-full h-full bg-[#1A1A1A] flex items-center justify-center text-xs text-gray-500 font-medium">
          S{shot.shot_id}
        </div>
      )}

      {/* Analysis Status Indicators */}
      {isAnalyzed && (
        <div className="absolute bottom-1 right-1 w-2 h-2 bg-green-500 rounded-full shadow-sm" />
      )}
      {isAnalyzing && (
        <div className="absolute bottom-1 right-1 w-3 h-3 border-2 border-white border-t-[#5B4FCF] rounded-full animate-spin" />
      )}
      
      {/* Darken unselected thumbnails to keep focus on the current scene */}
      {!isCurrent && (
        <div className="absolute inset-0 bg-black/40 hover:bg-black/10 transition-colors" />
      )}
    </div>
  )
})
Thumbnail.displayName = 'Thumbnail'

export default function ShotTimeline() {
  const shots = useFilmStore((state) => state.shots)
  const currentShotId = useFilmStore((state) => state.currentShotId)
  const analyses = useFilmStore((state) => state.analyses)
  const isGlobalAnalyzing = useFilmStore((state) => state.isAnalyzing)
  const setSeekRequest = useFilmStore((state) => state.setSeekRequest)

  const parentRef = useRef<HTMLDivElement>(null)

  // Use TanStack Virtual to handle 50+ or thousands of shots easily
  const virtualizer = useVirtualizer({
    horizontal: true,
    count: shots.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Fixed 80px width
    overscan: 5, // Load 5 thumbnails out of frame ahead of time
  })

  // Automatically track central scrolling based on current playing shot
  useEffect(() => {
    if (currentShotId === null) return
    const index = shots.findIndex(s => s.shot_id === currentShotId)
    if (index !== -1) {
      virtualizer.scrollToIndex(index, { align: 'center', behavior: 'smooth' })
    }
  }, [currentShotId, shots, virtualizer])

  const handleThumbnailClick = (startTime: number) => {
    setSeekRequest(startTime + 0.5) 
  }

  return (
    <div 
      ref={parentRef} 
      className="w-full h-[56px] overflow-x-auto overflow-y-hidden bg-black hide-scrollbar"
    >
      <div
        style={{
          width: `${virtualizer.getTotalSize()}px`,
          height: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const shot = shots[virtualItem.index]
          if (!shot) return null

          const isCurrent = shot.shot_id === currentShotId
          const isAnalyzed = !!analyses[shot.shot_id]
          const isAnalyzing = !isAnalyzed && isGlobalAnalyzing

          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: `${virtualItem.size}px`,
                height: '100%',
                transform: `translateX(${virtualItem.start}px)`,
              }}
            >
              <Thumbnail 
                shot={shot}
                isCurrent={isCurrent}
                isAnalyzed={isAnalyzed}
                isAnalyzing={isAnalyzing}
                onClick={handleThumbnailClick}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
