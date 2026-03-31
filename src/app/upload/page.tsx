"use client"
import React, { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useFilmStore } from '../store/useFilmStore'
import { useTranslations } from 'next-intl'
import LanguageSwitcher from '../components/LanguageSwitcher'

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [director, setDirector] = useState('')
  const [titleEn, setTitleEn] = useState('')
  const [directorEn, setDirectorEn] = useState('')
  const [progress, setProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadDuration, setUploadDuration] = useState<number>(0)
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  const setJobId = useFilmStore(state => state.setJobId)
  const setVideoUrl = useFilmStore(state => state.setVideoUrl)
  const resetStore = useFilmStore(state => state.reset)
  
  const t = useTranslations('Upload')

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const validateAndSetFile = (selectedFile: File) => {
    setError(null)
    const validTypes = ['video/mp4', 'video/quicktime', 'video/x-matroska', 'video/avi']
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(mp4|mov|mkv|avi)$/i)) {
      setError(t('unsupportedFormat'))
      return
    }
    if (selectedFile.size > 4 * 1024 * 1024 * 1024) {
      setError(t('fileTooLarge'))
      return
    }
    
    // Read video duration locally to initialize analysis view correctly
    const videoNode = document.createElement('video')
    videoNode.preload = 'metadata'
    videoNode.onloadedmetadata = () => {
      setUploadDuration(videoNode.duration)
      URL.revokeObjectURL(videoNode.src)
      startUpload(selectedFile)
    }
    videoNode.src = URL.createObjectURL(selectedFile)
    setFile(selectedFile)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0])
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const startUpload = (uploadFile: File) => {
    // Clear previous state
    resetStore()
    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', uploadFile)
    formData.append('film_title', title || t('untitled'))
    formData.append('director', director || t('unknown'))
    formData.append('film_title_en', titleEn || '')
    formData.append('director_en', directorEn || '')
    
    // Inject locale target for AI prompts
    const isEn = document.cookie.includes('NEXT_LOCALE=en-US')
    formData.append('locale', isEn ? 'en-US' : 'zh-CN')

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

    const xhr = new XMLHttpRequest()
    // Open async POST request
    xhr.open('POST', `${API_URL}/api/upload`, true)
    
    // Track upload progress via XHR API
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        setProgress(Math.round((e.loaded / e.total) * 100))
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText)
          
          // Construct persistent local ObjectURL so video DOM doesn't re-download
          // Wait to connect to websocket upon transition
          const localUrl = URL.createObjectURL(uploadFile)
          setVideoUrl(localUrl)
          setJobId(res.job_id)
          
          // Switch route smoothly to layout screen
          router.push(`/analyze/${res.job_id}`)
        } catch (err) {
          setError(t('parseError'))
          setIsUploading(false)
        }
      } else {
        setError(t('httpError', { status: xhr.status }))
        setIsUploading(false)
      }
    }

    xhr.onerror = () => {
      setError(t('networkError'))
      setIsUploading(false)
    }

    xhr.send(formData)
  }

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6 text-white font-sans">
      <div className="absolute top-6 right-6 z-10">
        <LanguageSwitcher />
      </div>
      <div className="w-full max-w-2xl">
        <div className="text-center mb-10">
          <h1 className="text-[2.5rem] font-bold mb-3 tracking-tight text-[#E2E0FD]">{t('title')}</h1>
          <p className="text-gray-400 text-[15px]">{t('subtitle')}</p>
        </div>

        {!isUploading && (
          <div className="space-y-4 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[11px] text-gray-500 font-bold uppercase tracking-wider pl-1">{t('titleCn')}</label>
                <input 
                  type="text" 
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={t('placeholderCn')}
                  className="w-full bg-[#0F0F0F] border border-gray-800 rounded-xl px-4 py-3 text-[14px] focus:border-[#5B4FCF] focus:outline-none transition-colors placeholder:text-gray-600 shadow-inner"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[11px] text-gray-500 font-bold uppercase tracking-wider pl-1">{t('directorCn')}</label>
                <input 
                  type="text" 
                  value={director}
                  onChange={(e) => setDirector(e.target.value)}
                  placeholder={t('placeholderDirector')}
                  className="w-full bg-[#0F0F0F] border border-gray-800 rounded-xl px-4 py-3 text-[14px] focus:border-[#5B4FCF] focus:outline-none transition-colors placeholder:text-gray-600 shadow-inner"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[11px] text-gray-500 font-bold uppercase tracking-wider pl-1">{t('titleEn')}</label>
                <input 
                  type="text" 
                  value={titleEn}
                  onChange={(e) => setTitleEn(e.target.value)}
                  placeholder="e.g. In the Mood for Love"
                  className="w-full bg-[#0F0F0F] border border-gray-800 rounded-xl px-4 py-3 text-[14px] focus:border-[#5B4FCF] focus:outline-none transition-colors placeholder:text-gray-600 shadow-inner"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[11px] text-gray-500 font-bold uppercase tracking-wider pl-1">{t('directorEn')}</label>
                <input 
                  type="text" 
                  value={directorEn}
                  onChange={(e) => setDirectorEn(e.target.value)}
                  placeholder="e.g. Wong Kar-wai"
                  className="w-full bg-[#0F0F0F] border border-gray-800 rounded-xl px-4 py-3 text-[14px] focus:border-[#5B4FCF] focus:outline-none transition-colors placeholder:text-gray-600 shadow-inner"
                />
              </div>
            </div>
          </div>
        )}

        <div 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center h-[420px] border-2 border-dashed rounded-[20px] transition-all duration-300 ${
            isUploading ? 'border-gray-800 bg-[#0A0A0A] cursor-not-allowed' :
            isDragging ? 'border-[#5B4FCF] bg-[#5B4FCF]/10 cursor-copy scale-[1.02]' : 
            'border-gray-700 bg-[#0F0F0F] hover:border-gray-500 hover:bg-[#1A1A1A] hover:shadow-lg cursor-pointer'
          }`}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            accept="video/mp4,video/quicktime,video/x-matroska,video/avi"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          
          {!isUploading ? (
            <div className="text-center px-6">
              <svg className="w-16 h-16 mx-auto text-gray-500 mb-5 relative group-hover:-translate-y-2 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div className="text-[19px] font-medium text-gray-200 mb-2">{t('dropArea')}</div>
              <div className="text-[13px] text-gray-500 font-medium">{t('supportedFormats')}</div>
              {error && <div className="mt-5 text-[13px] text-red-300 bg-red-900/30 px-4 py-2.5 rounded border border-red-900/50">{error}</div>}
            </div>
          ) : (
            <div className="w-4/5 max-w-md text-center">
              <div className="text-base font-semibold text-gray-100 mb-2 truncate">
                {file?.name}
              </div>
              <div className="text-[13px] text-gray-500 mb-8 font-mono">
                {t('duration', { duration: uploadDuration ? Math.round(uploadDuration) : '--' })} • {t('size', { size: (file!.size / (1024 * 1024)).toFixed(1) })}
              </div>
              
              <div className="w-full bg-gray-900 rounded-full h-[6px] mb-4 overflow-hidden border border-gray-800 shadow-inner">
                <div 
                  className="bg-gradient-to-r from-[#5B4FCF] to-[#7E74ED] h-full rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              
              <div className="flex justify-between text-[13px] tracking-wide text-gray-400 font-semibold">
                <span>{t('uploading')}</span>
                <span>{progress}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
