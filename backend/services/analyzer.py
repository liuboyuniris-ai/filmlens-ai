import asyncio
import base64
import json
import hashlib
import os
from dotenv import load_dotenv
load_dotenv(override=True)
from openai import AsyncOpenAI
from backend.models import Shot, ShotAnalysis, JobStatus, FilmContext, FilmResearchMap
from backend.prompts.shot_analysis import get_shot_analysis_prompt, build_context_header, SHOT_ANALYSIS_PROMPT
from backend.prompts.research_mapping import RESEARCH_MAPPING_PROMPT
from backend.database import save_shot_analysis
from backend.services.paper_search import fetch_paper_sources, fetch_google_scholar_serp
from backend.redis_client import get_redis_client
import httpx
from google import genai
from google.genai import types

# Load settings from environment
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

# Initialize OpenAI client
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY", OPENROUTER_KEY)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-flash-1.5")

client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

# Initialize Native Google SDK
native_client = None
if LLM_API_KEY and LLM_API_KEY.startswith("AIza"):
    print(f"[Analyzer] Initializing native Google SDK for model: {LLM_MODEL}")
    native_client = genai.Client(api_key=LLM_API_KEY)

def format_time(secs: float) -> str:
    m, s = divmod(int(secs), 60)
    return f"{m:02d}:{s:02d}"

async def fetch_film_criticism(film_title: str, director: str, api_key: str, redis_client) -> list[str]:
    """
    Fetch film analysis papers' abstracts from Semantic Scholar API.
    """
    if not api_key:
        return []

    cache_key = f"rag_film:{film_title}:{director}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"[RAG Cache Error] {e}")

    try:
        query = f"{director} {film_title} film analysis cinematography"
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "fields": "title,abstract,year",
            "limit": 5
        }
        headers = {"x-api-key": api_key}
        
        async with httpx.AsyncClient() as client:
             response = await client.get(url, params=params, headers=headers, timeout=10.0)
             if response.status_code == 200:
                 data = response.json()
                 papers = data.get("data", [])
                 snippets = []
                 for p in papers:
                     abstract = p.get("abstract") or ""
                     if len(abstract) > 100:
                         snippets.append(abstract)
                     if len(snippets) >= 3:
                         break
                 
                 # Cache for 7 days
                 await redis_client.setex(cache_key, 604800, json.dumps(snippets, ensure_ascii=False))
                 return snippets
    except Exception as e:
        print(f"[RAG API Error] {e}")

    return []

def build_rag_injection(snippets: list[str]) -> str:
    """
    Format retrieved abstracts into a prompt snippet.
    """
    if not snippets:
        return ""

    header = "══════════════════════════════════════════\nAcademic Criticism Reference (from Semantic Scholar)\n══════════════════════════════════════════\nBelow are real academic analysis snippets for this film or director.\nReference these for stylistic and theoretical inspiration without direct copying:\n\n"
    content = ""
    for i, snippet in enumerate(snippets):
        content += f"[{i+1}] {snippet[:300]}...\n\n"
    
    return header + content + "\n"

async def publish_event(job_id: str, event_data: dict):
    r = get_redis_client()
    try:
        payload = json.dumps(event_data, ensure_ascii=False)
        await r.publish(f"channel:{job_id}", payload)
    except Exception as e:
        print(f"[Redis ERROR] Event publish failed: {e}")

async def analyze_shot(shot: Shot, job_id: str, all_shots: list[Shot], job: JobStatus = None, locale: str = "zh-CN", use_rag: bool = False) -> ShotAnalysis:
    if not os.path.exists(shot.keyframe_path):
        raise FileNotFoundError(f"Keyframe not found: {shot.keyframe_path}")

    with open(shot.keyframe_path, "rb") as image_file:
        image_bytes = image_file.read()
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        frame_md5 = hashlib.md5(image_bytes).hexdigest()
    
    r = get_redis_client()
    cache_key = f"cache:{frame_md5}"
    
    cached_result = await r.get(cache_key)
    if cached_result:
        print(f"[Cache Hit] Shot {shot.shot_id} via MD5 hash")
        data = json.loads(cached_result)
    else:
        # Step 1: Find prev/next shots
        prev_shot = all_shots[shot.shot_id - 2] if shot.shot_id > 1 else None
        next_shot = all_shots[shot.shot_id] if shot.shot_id < len(all_shots) else None

        # Step 2: Build preceding_shots_desc
        preceding_lines = []
        if job and job.analyses:
            # Look at up to 3 previously analyzed shots
            for i in range(max(1, shot.shot_id - 3), shot.shot_id):
                if i in job.analyses:
                    a = job.analyses[i]
                    preceding_lines.append(f"Shot {i}：{a.shot_scale} · {a.camera_movement} · {a.editing.rhythm_feel}")
        preceding_shots_desc = "\n".join(preceding_lines)

        # Defaults
        f_context = job.film_context if job else None
        film_title = f_context.film_title if f_context else "未命名影片"
        director = f_context.director if f_context else "未知导演"
        production_year = f_context.production_year if f_context else 2024
        country = f_context.country_of_production if f_context else "未知国家"
        film_summary = f_context.summary if f_context else ""

        header = build_context_header(
            film_title=film_title,
            director=director,
            production_year=production_year,
            country=country,
            shot_id=shot.shot_id,
            total_shots=len(all_shots),
            timecode=format_time(shot.start_time),
            total_duration=format_time(all_shots[-1].end_time) if all_shots else "00:00",
            film_summary=film_summary,
            preceding_shots_desc=preceding_shots_desc
        )

        # RAG Logic
        rag_text = ""
        if use_rag:
            snippets = await fetch_film_criticism(
                film_title=film_title,
                director=director,
                api_key=SEMANTIC_SCHOLAR_API_KEY,
                redis_client=r,
            )
            rag_text = build_rag_injection(snippets)
        
        progress = (shot.shot_id / len(all_shots)) if all_shots else 0.5
        narrative_pos = "影片开场阶段" if progress < 0.1 else "影片收尾阶段" if progress > 0.9 else f"影片中段（第 {int(progress * 100)}% 处）"

        templated_prompt = SHOT_ANALYSIS_PROMPT.replace("[FILM_TITLE]", film_title).replace("[DIRECTOR]", director).replace("[NARRATIVE_POS]", narrative_pos)
        full_prompt = header + rag_text + templated_prompt

        # Step 3: Construct multi-part contents
        gemini_contents = []
        openai_messages_content = []

        def add_image_info(s, label):
            with open(s.keyframe_path, "rb") as f:
                img_bytes = f.read()
                b64 = base64.b64encode(img_bytes).decode()
                if native_client:
                    gemini_contents.append(types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'))
                    gemini_contents.append(label)
                else:
                    openai_messages_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                    openai_messages_content.append({"type": "text", "text": label})

        if prev_shot and os.path.exists(prev_shot.keyframe_path):
            add_image_info(prev_shot, f"↑ 这是上一个镜头（Shot {prev_shot.shot_id}），仅供剪辑关系参考，不需要分析")

        # Current shot
        if native_client:
            gemini_contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))
            gemini_contents.append(f"↑ 这是【当前镜头】（Shot {shot.shot_id}），这是你需要深入分析的帧")
        else:
            openai_messages_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}})
            openai_messages_content.append({"type": "text", "text": f"↑ 这是【当前镜头】（Shot {shot.shot_id}），这是你需要深入分析的帧"})

        if next_shot and os.path.exists(next_shot.keyframe_path):
            add_image_info(next_shot, f"↑ 这是下一个镜头（Shot {next_shot.shot_id}），仅供剪辑关系参考，不需要分析")

        # Finally the prompt
        if native_client:
            gemini_contents.append(full_prompt)
        else:
            openai_messages_content.append({"type": "text", "text": full_prompt})

        if native_client:
            response = await asyncio.to_thread(
                native_client.models.generate_content,
                model=LLM_MODEL,
                contents=gemini_contents,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7)
            )
            data = json.loads(response.text)
        else:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": openai_messages_content}]
            )
            content = response.choices[0].message.content
            start_idx, end_idx = content.find('{'), content.rfind('}')
            if start_idx == -1 or end_idx == -1: raise ValueError("Invalid JSON response")
            data = json.loads(content[start_idx:end_idx+1])
        
        await r.setex(cache_key, 30 * 24 * 3600, json.dumps(data, ensure_ascii=False))

    # Defensive parsing
    editing_raw = data.get("editing", {})
    editing_data = {
        "cut_type_in": editing_raw.get("cut_type_in", "未知"),
        "cut_type_out": editing_raw.get("cut_type_out", "未知"),
        "rhythm_feel": editing_raw.get("rhythm_feel", "未知"),
        "prev_shot_relation": editing_raw.get("prev_shot_relation", "未知"),
        "next_shot_relation": editing_raw.get("next_shot_relation", "未知"),
        "editing_function": editing_raw.get("editing_function", "未知"),
        "specific_techniques": editing_raw.get("specific_techniques", []),
        "search_keywords_en": editing_raw.get("search_keywords_en", ["editing"]),
        "search_keywords_cn": editing_raw.get("search_keywords_cn", ["剪辑"])
    }
    
    analysis = ShotAnalysis(
        shot_id=shot.shot_id,
        shot_scale=data.get("shot_scale", "未知"),
        camera_movement=data.get("camera_movement", "未知"),
        camera_angle=data.get("camera_angle", "未知"),
        depth_of_field=data.get("depth_of_field", "未知"),
        lighting_scheme=data.get("lighting_scheme", "未知"),
        color_temperature=data.get("color_temperature", "未知"),
        dominant_colors=data.get("dominant_colors", []),
        primary_technique=data.get("primary_technique", "未知"),
        theoretical_connections=data.get("theoretical_connections", []) or [],
        motifs_symbols=data.get("motifs_symbols", []) or [],
        editing=editing_data,
        narrative_function=data.get("narrative_function", "未知"),
        contextual_analysis=data.get("contextual_analysis", ""),
        context_links=data.get("context_links", []) or []
    )
    
    await save_shot_analysis(job_id, analysis)
    
    # Notify & Cache
    analysis_payload = json.dumps({"event": "shot_analyzed", "shot_id": shot.shot_id, "analysis": analysis.model_dump()}, ensure_ascii=False)
    await r.publish(f"channel:{job_id}", analysis_payload)
    await r.hset(f"status:{job_id}:results", f"shot:{shot.shot_id}", analysis_payload)
    await r.incr(f"status:{job_id}:count")

    # Concurrent paper search
    asyncio.create_task(fetch_paper_sources(job_id, shot.shot_id, analysis.theoretical_connections))
    
    return analysis

async def process_shot_with_retry(shot: Shot, job_id: str, all_shots: list[Shot], job: JobStatus, semaphore: asyncio.Semaphore, locale: str = "zh-CN", use_rag: bool = False) -> ShotAnalysis | None:
    async with semaphore:
        retries = 3
        for attempt in range(retries + 1):
            try:
                return await analyze_shot(shot, job_id, all_shots, job, locale, use_rag=use_rag)
            except Exception as e:
                error_str = str(e)
                if attempt < retries and ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str):
                    wait_time = 20 * (2 ** attempt)
                    print(f"[Shot {shot.shot_id}] Rate limited. Retry in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < retries:
                    await asyncio.sleep(5)
                else:
                    print(f"[Shot {shot.shot_id}] Failed after {retries} retries: {e}")
                    await publish_event(job_id, {"event": "error", "shot_id": shot.shot_id, "message": f"镜头 {shot.shot_id} 分析彻底失败: {error_str}"})
        return None

async def analyze_all_shots(job_id: str, shots: list[Shot], locale: str = "zh-CN", job: JobStatus = None):
    semaphore = asyncio.Semaphore(3)
    tasks = []
    for shot in shots:
        tasks.append(process_shot_with_retry(shot, job_id, shots, job, semaphore, locale, use_rag=False))
    
    results = await asyncio.gather(*tasks)
    
    # Set progress count in redis for playback if needed
    r = get_redis_client()
    await r.setex(f"status:{job_id}:count", 3600, sum(1 for r in results if r))
    
    return results

async def generate_film_context(job_id: str, analyses: list[ShotAnalysis], locale: str = "zh-CN", initial_context: FilmContext = None):
    if not analyses: return initial_context
    
    scales = [a.shot_scale for a in analyses if a]
    movements = [a.camera_movement for a in analyses if a]
    theories = [t.theory_name_cn for a in analyses if a for t in a.theoretical_connections]
            
    summary_input = f"基本信息: 《{initial_context.film_title}》, 导演 {initial_context.director}\n镜头数: {len(analyses)}\n景别: {', '.join(set(scales[:15]))}\n运镜: {', '.join(set(movements[:15]))}\n理论: {', '.join(set(theories[:15]))}"
    prompt = f"你是一个电影论家。基于数据汇总，撰写一份宏观深度研报（JSON）。数据：{summary_input}\n字段：film_title, director, production_year, country_of_production, political, economic, cultural, gender_sexuality, postcolonial, technological, auteur_biography, summary, search_keywords_en (list), search_keywords_cn (list)。要求语言: {locale}"
    
    data = None
    try:
        if native_client:
            response = await asyncio.to_thread(native_client.models.generate_content, model=LLM_MODEL, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
            data = json.loads(response.text)
        else:
            response = await client.chat.completions.create(model=LLM_MODEL, messages=[{"role": "user", "content": prompt}])
            content = response.choices[0].message.content
            s, e = content.find('{'), content.rfind('}')
            data = json.loads(content[s:e+1]) if s != -1 else None
    except Exception as e:
        print(f"[Context Gen Error] {e}")

    if data:
        # Robust normalization for Pydantic validation
        def to_str(val, default=""):
            if isinstance(val, list): return ", ".join([str(x) for x in val])
            return str(val) if val is not None else default

        def to_int(val, default=2024):
            try: return int(val)
            except: return default

        context = FilmContext(
            job_id=job_id,
            film_title=to_str(data.get("film_title"), initial_context.film_title),
            director=to_str(data.get("director"), initial_context.director),
            production_year=to_int(data.get("production_year"), 2024),
            country_of_production=to_str(data.get("country_of_production"), "未知"),
            political=to_str(data.get("political"), "无法生成分析"),
            economic=to_str(data.get("economic"), "无法生成分析"),
            cultural=to_str(data.get("cultural"), "无法生成分析"),
            gender_sexuality=to_str(data.get("gender_sexuality"), "无法生成分析"),
            postcolonial=to_str(data.get("postcolonial"), "无法生成分析"),
            technological=to_str(data.get("technological"), "无法生成分析"),
            auteur_biography=to_str(data.get("auteur_biography"), "无法生成分析"),
            summary=to_str(data.get("summary"), "无法生成分析"),
            search_keywords_en=data.get("search_keywords_en", []),
            search_keywords_cn=data.get("search_keywords_cn", []),
            context_loaded=True
        )
    else:
        context = initial_context
        context.context_loaded = False
        context.context_error = "分析服务暂时不可用"

    # Cache & Publish
    r = get_redis_client()
    payload = json.dumps({"event": "film_context", "context": context.model_dump()}, ensure_ascii=False)
    await r.setex(f"status:{job_id}:context", 3600 * 24, payload)
    await r.publish(f"channel:{job_id}", payload)
    return context

async def generate_research_map(job_id: str, film_title: str, director: str) -> dict:
    """
    Search many papers and categorize them into themes/techniques using LLM.
    """
    r = get_redis_client()
    try:
        print(f"[ResearchMap] Generating for {film_title}...")
        
        # 1. Broad Search (S2 and Google Scholar via SerpApi)
        # Handle '未知' or 'Unknown' in director
        safe_director = "" if director in ["未知", "Unknown", "None", None] else director
        query = f"{safe_director} {film_title} film analysis scholarship".strip()
        
        snippets_for_llm = []
        async with httpx.AsyncClient() as http_client:
            # Task A: Semantic Scholar
            s2_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            s2_params = {
                "query": query,
                "fields": "title,abstract,authors,year,externalIds",
                "limit": 15
            }
            s2_headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY} if SEMANTIC_SCHOLAR_API_KEY and SEMANTIC_SCHOLAR_API_KEY != "your_key" else {}
            
            # Task B: Google Scholar (SerpApi)
            serp_task = fetch_google_scholar_serp(query, http_client)
            
            # Run S2 search
            s2_resp = await http_client.get(s2_url, params=s2_params, headers=s2_headers)
            if s2_resp.status_code == 200:
                s2_data = s2_resp.json()
                for p in s2_data.get("data", []):
                    title = p.get("title", "")
                    abstract = p.get("abstract") or ""
                    authors = ", ".join([a['name'] for a in p.get("authors", [])])
                    year = p.get("year") or "N/A"
                    link = f"https://www.semanticscholar.org/paper/{p.get('paperId')}"
                    if abstract:
                        snippets_for_llm.append(f"Source: Semantic Scholar\nTitle: {title}\nAuthor: {authors}\nYear: {year}\nURL: {link}\nAbstract: {abstract}")

            # Run SerpApi
            serp_results = await serp_task
            for p in serp_results:
                snippets_for_llm.append(f"Source: Google Scholar (SerpApi)\nTitle: {p['title']}\nAuthor: {p['author']}\nURL: {p['url']}\nAbstract: {p['abstract']}")

        if not snippets_for_llm:
            print("[ResearchMap] No papers found in any database.")
            # Fallback: Try a simpler query if empty
            if safe_director:
                 # Recursive call with just title might be too much, let's just try once more here
                 print("[ResearchMap] Retrying with just title...")
                 # ... (simplified logic for brevity or just continue)

        if not snippets_for_llm:
            print("[ResearchMap] No papers found.")
            # Notify done with empty
            empty_map = {"categories": []}
            await r.publish(f"channel:{job_id}", json.dumps({"event": "research_map_ready", "research_map": empty_map}, ensure_ascii=False))
            return empty_map

        # 2. LLM Categorization
        all_snippets_text = "\n\n---\n\n".join(snippets_for_llm)
        full_prompt = RESEARCH_MAPPING_PROMPT.replace("[ACADEMIC_SNIPPETS]", all_snippets_text)

        map_data = {"categories": []}
        if native_client:
            response = await asyncio.to_thread(
                native_client.models.generate_content,
                model=LLM_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3)
            )
            map_data = json.loads(response.text)
        else:
            # Global 'client' is the OpenAI client
            resp = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": full_prompt}]
            )
            content = resp.choices[0].message.content
            start_idx, end_idx = content.find('{'), content.rfind('}')
            map_data = json.loads(content[start_idx:end_idx+1])

        # 3. Save to Redis/Context
        # Validate through Pydantic model
        try:
            research_map_obj = FilmResearchMap(**map_data)
            map_to_save = research_map_obj.model_dump()
        except Exception as ve:
            print(f"[ResearchMap] Validation Error: {ve}. Sending raw as fallback.")
            map_to_save = map_data

        event_payload = {
            "event": "research_map_ready",
            "research_map": map_to_save
        }
        await r.publish(f"channel:{job_id}", json.dumps(event_payload, ensure_ascii=False))
        
        # Update context in redis
        context_data = await r.get(f"status:{job_id}:context")
        if context_data:
            msg_json = json.loads(context_data)
            # Ensure context has research_map field
            if "context" in msg_json:
                msg_json["context"]["research_map"] = map_to_save
                await r.setex(f"status:{job_id}:context", 3600 * 24, json.dumps(msg_json, ensure_ascii=False))
            
        print(f"[ResearchMap] Success for {film_title}")
        return map_to_save
    except Exception as e:
        print(f"[ResearchMap Error] {e}")
        import traceback
        traceback.print_exc()
        # Fallback event
        empty_map = {"categories": []}
        await r.publish(f"channel:{job_id}", json.dumps({"event": "research_map_ready", "research_map": empty_map}, ensure_ascii=False))
        return empty_map
