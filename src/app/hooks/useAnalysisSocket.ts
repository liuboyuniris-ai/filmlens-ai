"use client"
import { useEffect, useState, useRef } from 'react'
import { useFilmStore } from '../store/useFilmStore'

export function useAnalysisSocket(jobId: string | null) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)

  const setShots = useFilmStore(state => state.setShots)
  const receiveAnalysis = useFilmStore(state => state.receiveAnalysis)
  const receiveSources = useFilmStore(state => state.receiveSources)
  const setVideoUrl = useFilmStore(state => state.setVideoUrl)
  const setAnalyzing = useFilmStore(state => state.setAnalyzing)
  const setShootError = useFilmStore(state => state.setShootError)
  const setFilmContext = useFilmStore(state => state.setFilmContext)
  const addChatMessage = useFilmStore(state => state.addChatMessage)

  const sendMessage = (data: any) => {
    if (jobId === 'demo') {
      console.log("[Demo] Mocking message send:", data)
      if (data.event === 'chat_request') {
        setTimeout(() => {
          addChatMessage({
            id: Math.random().toString(36).substring(7),
            role: 'assistant',
            content: "This is a pre-analyzed demo. In the full version, the AI will answer your specific questions about this shot based on its deep cinematic analysis.",
            timestamp: Date.now(),
            shotId: data.shot_id
          })
        }, 1000)
      }
      return
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }

  useEffect(() => {
    if (!jobId) return

    // --- DEMO MODE SIMULATION ---
    if (jobId === 'demo') {
      setIsConnected(true)
      setAnalyzing(true)
      
      const runDemo = async () => {
        try {
          const res = await fetch('/demo/analysis.json')
          const data = await res.json()
          
          setVideoUrl('/demo/video.mp4')
          
          // Simulate latency for a "vibe"
          await new Promise(r => setTimeout(r, 800))
          setShots(data.shots)
          
          await new Promise(r => setTimeout(r, 500))
          setFilmContext(data.film_context)

          if (data.film_context.research_map) {
             setFilmContext({
                  ...data.film_context,
                  research_map: data.film_context.research_map
             })
          }

          // Progressively reveal analysis to look "live"
          const analyzes = Object.entries(data.analyses)
          for (const [id, analysis] of analyzes) {
            receiveAnalysis(Number(id), analysis as any)
            await new Promise(r => setTimeout(r, 400 + Math.random() * 600))
          }
          
          setAnalyzing(false)
        } catch (e) {
          console.error("[Demo] Error loading demo data:", e)
          setError("Failed to load demo data.")
        }
      }
      
      runDemo()
      return
    }

    let reconnectTimeout: NodeJS.Timeout
    const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"

    const connect = () => {
      if (wsRef.current && wsRef.current.readyState <= 1) return

      const finalUrl = `${WS_URL}/ws/${jobId}`
      console.log(`[Socket] Attempting connection to: ${finalUrl}`)
      const ws = new WebSocket(finalUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log(`[Socket] Connection fully opened for job ${jobId}`)
        setIsConnected(true)
        setError(null)
        reconnectAttempts.current = 0
        setAnalyzing(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          switch (data.event) {
            case "shots_detected":
              // Allows rendering timeline before AI completes processing
              setShots(data.shots)
              break
            case "shot_analyzed":
              // Processed progressively per shot
              receiveAnalysis(data.shot_id, data.analysis)
              break
            case "sources_ready":
              // Injected dynamically resolving latency discrepancy 
              receiveSources(data.shot_id, data.theory_name_en, data.sources)
              break
            case "film_context":
              setFilmContext(data.context)
              break
            case "chat_response":
              addChatMessage({
                id: Math.random().toString(36).substring(7),
                role: 'assistant',
                content: data.answer,
                timestamp: Date.now(),
                shotId: data.ref_shot_id
              })
              break

            case "complete":
              setAnalyzing(false)
              break
            case "error":
              setShootError(data.shot_id, data.message)
              break
            case "video_ready":
              const API_BASE = WS_URL.replace("ws://", "http://").replace("wss://", "https://")
              const cleanBase = API_BASE.endsWith('/') ? API_BASE.slice(0, -1) : API_BASE
              const cleanPath = data.video_url.startsWith('/') ? data.video_url : `/${data.video_url}`
              const staticUrl = `${cleanBase}${cleanPath}`
              console.log("[Video] Static MP4 ready:", staticUrl)
              
              // Only switch if we don't have a local blob (e.g. on refresh)
              const currentVideoUrl = useFilmStore.getState().videoUrl
              if (!currentVideoUrl || !currentVideoUrl.startsWith('blob:')) {
                setVideoUrl(staticUrl)
              } else {
                console.log("[Video] Keeping local blob for stability.")
              }
              break;
            case "pipeline_started":
              console.log("[Pipeline] Started:", data.message)
              break
            case "research_map_ready":
              console.log("[ResearchMap] Received map:", data.research_map)
              if (useFilmStore.getState().filmContext) {
                setFilmContext({
                  ...useFilmStore.getState().filmContext!,
                  research_map: data.research_map
                })
              }
              break
            case "ws_connected":
              console.log("WebSocket connected successfully:", data.message)
              break
            default:
              console.warn("Unhandled WS event:", data.event)
          }
        } catch (e) {
          console.error("Failed to parse WS message", e)
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null

        // Exponential backoff reconnect
        if (reconnectAttempts.current < 5) {
          // 1s, 2s, 4s, 8s, 16s
          const delay = Math.pow(2, reconnectAttempts.current) * 1000
          reconnectAttempts.current += 1

          reconnectTimeout = setTimeout(connect, delay)
        } else {
          setError("Connection lost. Max reconnect attempts reached.")
          setAnalyzing(false)
        }
      }

      ws.onerror = (e) => {
        console.error(`[Socket] WebSocket error for job ${jobId}:`, e)
        console.log(`[Socket] Current readyState: ${ws.readyState}`)
      }
    }

    connect()

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (wsRef.current) {
        // Suppress onclose reconnect behavior during teardown
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [jobId, setShots, receiveAnalysis, receiveSources, setAnalyzing, setShootError, setFilmContext, setVideoUrl, addChatMessage])

  return { isConnected, error, sendMessage }
}
