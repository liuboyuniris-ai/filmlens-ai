"use client"
import React, { useRef, useEffect, useState } from 'react'
import { useFilmStore } from '../../store/useFilmStore'

interface VideoPlayerProps {
  src: string
}

export default function VideoPlayer({ src }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  
  // Connect to Zustand store
  const shots = useFilmStore((state) => state.shots)
  const analyses = useFilmStore((state) => state.analyses)
  const currentShotId = useFilmStore((state) => state.currentShotId)
  const currentTime = useFilmStore((state) => state.currentTime)
  const setCurrentTime = useFilmStore((state) => state.setCurrentTime)
  const seekRequest = useFilmStore((state) => state.seekRequest)
  const setSeekRequest = useFilmStore((state) => state.setSeekRequest)

  const [duration, setDuration] = useState(0)
  const [videoError, setVideoError] = useState<string | null>(null)
  
  // Re-load video when source changes to ensure smooth transition from blob to static URL
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load()
    }
  }, [src])

  // Handle seek requests from externally (like ShotTimeline)
  useEffect(() => {
    if (seekRequest !== null && videoRef.current) {
      videoRef.current.currentTime = seekRequest
      setSeekRequest(null)
    }
  }, [seekRequest, setSeekRequest])

  // Native video timeupdate handler (updates global store)
  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    
    // Performance note: Only sync the store value to avoid large re-renders. 
    // Zustand specifically handles the precise condition.
    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime)
    }
    
    const handleLoadedMetadata = () => {
      setDuration(video.duration)
    }

    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
    }
  }, [setCurrentTime])

  // Get color representing specific shot scales
  const getSegmentColor = (shotId: number) => {
    const scale = analyses[shotId]?.shot_scale || ''
    if (['大特写', '特写'].includes(scale)) return '#AFA9EC'
    if (['中近景', '中景'].includes(scale)) return '#5DCAA5'
    if (['中远景', '远景', '大远景'].includes(scale)) return '#F0997B'
    return '#4B5563' // Default gray for unanalyzed or unclassified
  }

  const handleSegmentClick = (e: React.MouseEvent, startTime: number) => {
    e.stopPropagation()
    if (videoRef.current) {
      videoRef.current.currentTime = startTime + 0.5
    }
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) videoRef.current.play()
      else videoRef.current.pause()
    }
  }

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return '00:00'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const currentShot = shots.find(s => s.shot_id === currentShotId)

  return (
    <div className="relative w-full aspect-video bg-black flex flex-col group overflow-hidden">
      {/* 6. Current Shot Label */}
      <div 
        className={`absolute top-4 left-4 z-10 bg-black/60 text-white px-3 py-1.5 rounded text-sm font-medium backdrop-blur-sm transition-opacity duration-150 ${currentShotId ? 'opacity-100' : 'opacity-0'}`}
      >
        Scene {currentShotId} {currentShot && `· ${formatTime(currentShot.start_time)}`}
      </div>

      {videoError && (
        <div className="absolute inset-0 z-20 bg-black/90 flex flex-col items-center justify-center p-6 text-center">
          <svg className="w-12 h-12 text-red-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <div className="text-white font-bold mb-2">视频加载失败</div>
          <div className="text-red-400 text-xs mb-4 font-mono max-w-full break-all px-4">{videoError}</div>
          <p className="text-gray-500 text-[11px] leading-relaxed">
            这可能是由于视频服务地址无法在当前浏览器中访问，<br />
            或转码后的编码格式不被当前环境支持。
          </p>
          <button 
            onClick={() => { setVideoError(null); videoRef.current?.load(); }}
            className="mt-6 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg text-xs font-bold transition-colors"
          >
            重试加载
          </button>
        </div>
      )}

      <video 
        ref={videoRef}
        src={src}
        className="w-full h-full object-contain cursor-pointer"
        controls={false}
        onClick={togglePlay}
        onError={(e) => {
          const video = e.currentTarget;
          const mediaError = video.error;
          let msg = "未知媒体解析错误";
          if (mediaError) {
            const codes: Record<number, string> = {
              1: "MEDIA_ERR_ABORTED",
              2: "MEDIA_ERR_NETWORK",
              3: "MEDIA_ERR_DECODE",
              4: "MEDIA_ERR_SRC_NOT_SUPPORTED"
            };
            msg = codes[mediaError.code] || `CODE_${mediaError.code}`;
            if (mediaError.message) msg += `: ${mediaError.message}`;
          }
          console.error("[VideoPlayer] Detail Error:", {
            code: mediaError?.code,
            msg,
            currentSrc: video.currentSrc || src,
            readyState: video.readyState,
            networkState: video.networkState
          });
          setVideoError(`${msg} (${video.currentSrc || src})`);
        }}
      />
      
      {/* Custom Timeline Controls Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end">
        {/* Playback Controls Component */}
        <div className="flex items-center space-x-4 mb-2">
          <button 
            onClick={togglePlay}
            className="text-white hover:text-gray-300 focus:outline-none"
          >
            {videoRef.current?.paused ? (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" /></svg>
            )}
          </button>
          <div className="text-white text-sm font-medium tabular-nums shadow-sm">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* 2. Timeline Strip Progress */}
        <div className="relative w-full h-3 bg-gray-800 rounded cursor-pointer group/timeline">
          {duration > 0 && shots.map((shot) => {
            const widthPct = (shot.duration / duration) * 100
            const leftPct = (shot.start_time / duration) * 100
            const isCurrent = currentShotId === shot.shot_id
            
            return (
              <div 
                key={shot.shot_id}
                onClick={(e) => handleSegmentClick(e, shot.start_time)}
                className={`absolute h-full group/segment ${isCurrent ? 'border shadow-[0_0_8px_rgba(255,255,255,0.5)] z-10 box-border border-white' : ''}`}
                style={{
                  left: `${leftPct}%`,
                  width: `${widthPct}%`,
                  backgroundColor: getSegmentColor(shot.shot_id),
                }}
              >
                {/* 3. Cut Point Line */}
                <div className="absolute left-0 top-0 bottom-0 w-[1px] bg-white/40 pointer-events-none" />
                
                {/* 5. Hover Tooltip (Basic HTML/CSS approach) */}
                <div className="absolute bottom-full left-[5%] mb-2 hidden group-hover/segment:block bg-black/90 tracking-wide text-white text-xs px-2 py-1 rounded shadow whitespace-nowrap z-20 pointer-events-none transform -translate-x-1/2">
                  Scene {shot.shot_id} • {formatTime(shot.start_time)}
                </div>
              </div>
            )
          })}
          
          {/* 4. Playhead Locator Marker */}
          <div 
            className="absolute top-1/2 -translate-y-1/2 w-1 h-5 rounded-full bg-white shadow-[0_2px_4px_rgba(0,0,0,0.5)] z-20 pointer-events-none"
            style={{ left: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
          />
        </div>
      </div>
    </div>
  )
}
