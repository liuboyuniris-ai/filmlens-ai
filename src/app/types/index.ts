export interface PaperSource {
  database: string
  region: 'CN' | 'US' | 'EU' | 'INTL'
  title: string
  title_cn: string
  title_en: string
  author: string
  year: number
  journal: string
  volume_issue: string
  pages: string
  url: string
  doi: string
  is_open_access: boolean
  pdf_url: string
  citation_count: number
}

export interface ResearchPaper {
  title: string
  author: string
  year: number
  url: string
  excerpt: string
  language: 'en' | 'zh-CN'
}

export interface PaperCitationCategory {
  category_name: string
  description: string
  papers: ResearchPaper[]
}

export interface FilmResearchMap {
  categories: PaperCitationCategory[]
}

export interface TheoryRef {
  theory_name_cn: string
  theory_name_en: string
  theorist_cn: string
  theorist_en: string
  year: number
  description: string
  search_keywords_en: string[]
  search_keywords_cn: string[]
  sources: PaperSource[]
  sources_loaded: boolean
  sources_error: string
}

export interface MotifSymbol {
  name_cn: string
  name_en: string
  category: 'object' | 'color' | 'space' | 'body' | 'light' | 'sound' | 'other'
  visual_description: string
  symbolic_meaning: string
  recurrence_in_film: number
  first_appearance_shot_id: number | null
  search_keywords_en: string[]
  search_keywords_cn: string[]
  sources: PaperSource[]
  sources_loaded: boolean
  sources_error: string
}

export interface EditingAnalysis {
  cut_type_in: string
  cut_type_out: string
  rhythm_feel: 'very_fast' | 'fast' | 'medium' | 'slow' | 'very_slow'
  prev_shot_relation: string
  next_shot_relation: string
  editing_function: string
  specific_techniques: string[]
  search_keywords_en: string[]
  search_keywords_cn: string[]
  sources: PaperSource[]
  sources_loaded: boolean
  sources_error: string
}

export interface ShotContextLink {
  context_dimension: 'political' | 'economic' | 'cultural' | 'gender_sexuality' | 'postcolonial' | 'technological' | 'auteur_biography' | 'other'
  visual_element: string
  connection: string
  confidence: 'strong' | 'moderate' | 'speculative'
  search_keywords_en: string[]
  search_keywords_cn: string[]
  sources: PaperSource[]
  sources_loaded: boolean
  sources_error: string
}

export interface FilmContext {
  job_id: string
  film_title: string
  director: string
  production_year: number
  country_of_production: string
  political: string
  economic: string
  cultural: string
  gender_sexuality: string
  postcolonial: string
  technological: string
  auteur_biography: string
  summary: string
  search_keywords_en: string[]
  search_keywords_cn: string[]
  sources: PaperSource[]
  sources_loaded: boolean
  sources_error: string
  research_map: FilmResearchMap
  context_loaded: boolean
  context_error: string
}

export interface Shot {
  shot_id: number
  start_time: number
  end_time: number
  duration: number
  keyframe_path: string
  keyframe_url: string
}

export interface ShotAnalysis {
  shot_id: number
  shot_scale: string
  camera_movement: string
  camera_angle: string
  depth_of_field: string
  lighting_scheme: string
  color_temperature: string
  dominant_colors: string[]
  primary_technique: string
  theoretical_connections: TheoryRef[]
  motifs_symbols: MotifSymbol[]
  editing: EditingAnalysis
  narrative_function: string
  contextual_analysis: string
  context_links: ShotContextLink[]
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'context_generating' | 'detecting' | 'analyzing' | 'done' | 'error'
  total_shots: number
  analyzed_shots: number
  sources_loaded_shots: number
  film_context: FilmContext | null
  shots: Shot[]
  analyses: Record<number, ShotAnalysis>
  error_message: string
}
