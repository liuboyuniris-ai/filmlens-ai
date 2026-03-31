import { create } from 'zustand'
import { Shot, ShotAnalysis } from '../types'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  shotId?: number
}

interface FilmState {
  jobId: string | null
  videoUrl: string | null
  shots: Shot[]
  analyses: Record<number, ShotAnalysis>
  currentShotId: number | null
  currentTime: number
  seekRequest: number | null
  isAnalyzing: boolean
  analyzedCount: number
  filmContext: any | null
  shotErrors: Record<number, string>
  chatMessages: ChatMessage[]

  setJobId: (id: string | null) => void
  setVideoUrl: (url: string | null) => void
  setShots: (shots: Shot[]) => void
  setCurrentTime: (time: number) => void
  setSeekRequest: (time: number | null) => void
  receiveAnalysis: (shotId: number, analysis: ShotAnalysis) => void
  receiveSources: (shotId: number, theoryNameEn: string, sources: any[]) => void
  setShootError: (shotId: number, message: string) => void
  findShotByTime: (time: number) => Shot | null
  setAnalyzing: (status: boolean) => void
  setFilmContext: (context: any) => void
  addChatMessage: (msg: ChatMessage) => void
  reset: () => void
}

const initialState = {
  jobId: null,
  videoUrl: null,
  shots: [],
  analyses: {},
  currentShotId: null,
  currentTime: 0,
  seekRequest: null,
  isAnalyzing: false,
  analyzedCount: 0,
  filmContext: null,
  shotErrors: {},
  chatMessages: [],
}

export const useFilmStore = create<FilmState>((set, get) => ({
  ...initialState,

  setJobId: (id) => set({ jobId: id }),
  setVideoUrl: (url) => set({ videoUrl: url }),
  setShots: (shots) => {
    set({ shots })
    // If no shot is selected, try to find one for the current time (usually 0)
    const { currentTime, currentShotId } = get()
    if (currentShotId === null && shots.length > 0) {
      const firstShot = shots.find(s => currentTime >= s.start_time && currentTime < s.end_time) || shots[0]
      set({ currentShotId: firstShot.shot_id })
    }
  },
  setAnalyzing: (status) => set({ isAnalyzing: status }),
  setSeekRequest: (time) => set({ seekRequest: time }),

  setCurrentTime: (time) => {
    const { shots, currentShotId } = get()

    // Binary search for the current shot based on time
    let low = 0
    let high = shots.length - 1
    let foundShotId: number | null = null

    while (low <= high) {
      const mid = Math.floor((low + high) / 2)
      const shot = shots[mid]

      if (time >= shot.start_time && time < shot.end_time) {
        foundShotId = shot.shot_id
        break
      } else if (time < shot.start_time) {
        high = mid - 1
      } else {
        low = mid + 1
      }
    }

    set((state) => {
      const updates: Partial<FilmState> = {}
      if (state.currentTime !== time) updates.currentTime = time

      // Allow re-finding if shots was previously empty
      if (foundShotId !== null && state.currentShotId !== foundShotId) {
        updates.currentShotId = foundShotId
      } else if (state.currentShotId === null && shots.length > 0) {
        // Fallback for initial state
        const initialShot = shots.find(s => time >= s.start_time && time < s.end_time) || shots[0]
        updates.currentShotId = initialShot.shot_id
      }

      return updates
    })
  },

  receiveAnalysis: (shotId, analysis) => {
    set((state) => {
      const newAnalyses = { ...state.analyses, [shotId]: analysis }
      return {
        analyses: newAnalyses,
        analyzedCount: Object.keys(newAnalyses).length
      }
    })
  },

  receiveSources: (shotId, theoryNameEn, sources) => {
    set((state) => {
      const analysis = state.analyses[shotId]
      if (!analysis) return state // Ignore if analysis hasn't landed yet

      const updatedConnections = (analysis.theoretical_connections || []).map(t => {
        if (t.theory_name_en === theoryNameEn) {
          return { ...t, sources, sources_loaded: true }
        }
        return t
      })

      return {
        analyses: {
          ...state.analyses,
          [shotId]: {
            ...analysis,
            theoretical_connections: updatedConnections
          }
        }
      }
    })
  },

  setShootError: (shotId, message) => {
    set((state) => ({
      shotErrors: { ...state.shotErrors, [shotId]: message }
    }))
  },

  findShotByTime: (time) => {
    const { shots } = get()
    let low = 0
    let high = shots.length - 1
    while (low <= high) {
      const mid = Math.floor((low + high) / 2)
      const shot = shots[mid]
      if (time >= shot.start_time && time < shot.end_time) {
        return shot
      } else if (time < shot.start_time) {
        high = mid - 1
      } else {
        low = mid + 1
      }
    }
    return null
  },

  setFilmContext: (context) => set({ filmContext: context }),
  addChatMessage: (msg) => set((state) => ({
    chatMessages: [...state.chatMessages, msg]
  })),
  reset: () => set(initialState)
}))
