from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict

class PaperSource(BaseModel):
    database: str
    region: str
    title: str
    title_cn: str = ""
    title_en: str = ""
    author: str
    year: int
    journal: str = ""
    volume_issue: str = ""
    pages: str = ""
    url: str
    doi: str = ""
    is_open_access: bool = False
    pdf_url: str = ""
    citation_count: int = 0

    def to_apa(self) -> str:
        pages_part = f", {self.pages}" if self.pages else ""
        vol_part = f", {self.volume_issue}" if self.volume_issue else ""
        doi_part = f". https://doi.org/{self.doi}" if self.doi else ""
        journal_part = f". {self.journal}{vol_part}{pages_part}" if self.journal else ""
        return f"{self.author} ({self.year}). {self.title}{journal_part}{doi_part}"

class ResearchPaper(BaseModel):
    title: str
    author: str
    year: int
    url: str
    excerpt: str  # The original argument/excerpt
    language: str # "en" or "zh-CN"

class PaperCitationCategory(BaseModel):
    category_name: str
    description: str
    papers: List[ResearchPaper]

class FilmResearchMap(BaseModel):
    categories: List[PaperCitationCategory] = []

class TheoryRef(BaseModel):
    theory_name_cn: str
    theory_name_en: str
    theorist_cn: str
    theorist_en: str
    year: int
    description: str
    search_keywords_en: List[str]
    search_keywords_cn: List[str]
    sources: List[PaperSource] = []
    sources_loaded: bool = False
    sources_error: str = ""

class MotifSymbol(BaseModel):
    name_cn: str
    name_en: str
    category: str
    visual_description: str
    symbolic_meaning: str
    recurrence_in_film: int = 0
    first_appearance_shot_id: Optional[int] = None
    search_keywords_en: List[str]
    search_keywords_cn: List[str]
    sources: List[PaperSource] = []
    sources_loaded: bool = False
    sources_error: str = ""

class EditingAnalysis(BaseModel):
    cut_type_in: str
    cut_type_out: str
    rhythm_feel: str
    prev_shot_relation: str
    next_shot_relation: str
    editing_function: str
    specific_techniques: List[str]
    search_keywords_en: List[str]
    search_keywords_cn: List[str]
    sources: List[PaperSource] = []
    sources_loaded: bool = False
    sources_error: str = ""

class ShotContextLink(BaseModel):
    context_dimension: str
    visual_element: str
    connection: str
    confidence: str
    search_keywords_en: List[str]
    search_keywords_cn: List[str]
    sources: List[PaperSource] = []
    sources_loaded: bool = False
    sources_error: str = ""

class FilmContext(BaseModel):
    job_id: str
    film_title: str
    director: str
    production_year: int
    country_of_production: str
    political: str
    economic: str
    cultural: str
    gender_sexuality: str
    postcolonial: str
    technological: str
    auteur_biography: str
    summary: str
    search_keywords_en: List[str]
    search_keywords_cn: List[str]
    sources: List[PaperSource] = []
    sources_loaded: bool = False
    sources_error: str = ""
    research_map: FilmResearchMap = FilmResearchMap()
    context_loaded: bool = False
    context_error: str = ""

class Shot(BaseModel):
    shot_id: int
    start_time: float
    end_time: float
    duration: float
    keyframe_path: str
    keyframe_url: str

class ShotAnalysis(BaseModel):
    shot_id: int
    shot_scale: str
    camera_movement: str
    camera_angle: str
    depth_of_field: str
    lighting_scheme: str
    color_temperature: str
    dominant_colors: List[str]
    primary_technique: str
    theoretical_connections: List[TheoryRef] = []
    motifs_symbols: List[MotifSymbol] = []
    editing: EditingAnalysis
    narrative_function: str
    contextual_analysis: str = ""
    context_links: List[ShotContextLink] = []

    model_config = ConfigDict(frozen=True)

class JobStatus(BaseModel):
    job_id: str
    status: str
    total_shots: int = 0
    analyzed_shots: int = 0
    sources_loaded_shots: int = 0
    film_context: Optional[FilmContext] = None
    shots: List[Shot] = []
    analyses: Dict[int, ShotAnalysis] = {}
    error_message: str = ""
