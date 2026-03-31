import os
import json
import asyncio
from urllib.parse import quote
import httpx
import redis.asyncio as redis
from typing import List, Dict, Any

from backend.models import TheoryRef, PaperSource

DATABASE_DISPLAY = {
    "SemanticScholar": {"label": "Semantic Scholar", "region": "INTL", "color": "#1857B6", "badge": "S2"},
    "CrossRef":        {"label": "CrossRef / DOI",   "region": "INTL", "color": "#E18335", "badge": "DOI"},
    "CNKI":            {"label": "中国知网 CNKI",     "region": "CN",   "color": "#DE2910", "badge": "知"},
    "JSTOR":           {"label": "JSTOR",             "region": "US",   "color": "#2B5797", "badge": "J"},
    "GoogleScholar":   {"label": "Google Scholar",    "region": "INTL", "color": "#4285F4", "badge": "G"},
    "WanFang":         {"label": "万方数据",           "region": "CN",   "color": "#C0392B", "badge": "万"},
    "VIP":             {"label": "维普期刊",           "region": "CN",   "color": "#E74C3C", "badge": "维"},
    "ProQuest":        {"label": "ProQuest",          "region": "US",   "color": "#003865", "badge": "PQ"},
    "PhilPapers":      {"label": "PhilPapers",        "region": "INTL", "color": "#5B4FCF", "badge": "PP"},
}

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
CNKI_API_KEY = os.getenv("CNKI_API_KEY", "")
CROSSREF_EMAIL = os.getenv("CROSSREF_EMAIL", "")
SERP_API_KEY = os.getenv("SERP_API_KEY", "")

async def fetch_semantic_scholar(theory: TheoryRef, client: httpx.AsyncClient) -> List[PaperSource]:
    query = " ".join(theory.search_keywords_en)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "fields": "title,authors,year,externalIds,citationCount,openAccessPdf,journal",
        "limit": 5
    }
    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY
    
    results = []
    try:
        response = await client.get(url, params=params, headers=headers, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("data", []):
                authors = item.get("authors", [])
                author_name = authors[0]["name"] if authors else "Unknown"
                
                open_access_pdf = item.get("openAccessPdf")
                is_open_access = bool(open_access_pdf)
                pdf_url = open_access_pdf.get("url", "") if open_access_pdf else ""
                
                paper_id = item.get("paperId", "")
                external_ids = item.get("externalIds", {})
                doi = external_ids.get("DOI", "")
                
                paper_url = pdf_url if pdf_url else f"https://www.semanticscholar.org/paper/{paper_id}"
                
                journal_dict = item.get("journal", {})
                journal_name = journal_dict.get("name", "") if journal_dict else ""

                results.append(PaperSource(
                    database="SemanticScholar",
                    region="INTL",
                    title=item.get("title", ""),
                    author=author_name,
                    year=item.get("year") or theory.year,
                    journal=journal_name,
                    url=paper_url,
                    doi=doi,
                    is_open_access=is_open_access,
                    pdf_url=pdf_url,
                    citation_count=item.get("citationCount") or 0
                ))
    except Exception as e:
        print(f"Semantic Scholar mapping error: {e}")
    return results

async def fetch_crossref(theory: TheoryRef, client: httpx.AsyncClient) -> List[PaperSource]:
    query = f"{theory.theory_name_en} {theory.theorist_en}"
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": 3
    }
    if CROSSREF_EMAIL:
        params["mailto"] = CROSSREF_EMAIL
        
    results = []
    try:
        response = await client.get(url, params=params, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("message", {}).get("items", []):
                doi = item.get("DOI", "")
                paper_url = f"https://doi.org/{doi}" if doi else item.get("URL", "")
                
                authors_data = item.get("author", [])
                if authors_data:
                    first_author = authors_data[0]
                    author_name = f"{first_author.get('given', '')} {first_author.get('family', '')}".strip()
                else:
                    author_name = "Unknown"
                    
                journal_list = item.get("container-title", [])
                journal_name = journal_list[0] if journal_list else ""
                
                pub_date = item.get("published-print", {}).get("date-parts", [[theory.year]])
                year = pub_date[0][0] if pub_date and pub_date[0] else theory.year
                
                titles = item.get("title", [])
                title = titles[0] if titles else "Unknown Title"

                results.append(PaperSource(
                    database="CrossRef",
                    region="INTL",
                    title=title,
                    author=author_name,
                    year=year,
                    journal=journal_name,
                    url=paper_url,
                    doi=doi,
                    is_open_access=False
                ))
    except Exception as e:
        print(f"CrossRef mapping error: {e}")
    return results

async def fetch_cnki(theory: TheoryRef, client: httpx.AsyncClient) -> List[PaperSource]:
    # 若无CNKI_API_KEY，直接构造静态链接用于兜底
    if not CNKI_API_KEY:
        url = f"https://kns.cnki.net/kns8/defaultresult/index?kw={quote(theory.theory_name_cn)}&korder=SU"
        return [PaperSource(
            database="CNKI",
            region="CN",
            title=f"在 知网 搜索：{theory.theory_name_cn}",
            author=theory.theorist_cn,
            year=theory.year,
            url=url
        )]
    
    # Placeholder for actual API call if CNKI_API_KEY is presented.
    url = "https://api.cnki.net/v1/search"
    params = {
        "keyword": f"{theory.theory_name_cn} 电影",
        "database": "CJFD",
        "pageSize": 3
    }
    headers = {"Authorization": f"Bearer {CNKI_API_KEY}"}
    
    results = []
    try:
        response = await client.get(url, params=params, headers=headers, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("records", []):
                results.append(PaperSource(
                    database="CNKI",
                    region="CN",
                    title=item.get("title", ""),
                    author=item.get("author", "Unknown"),
                    year=int(item.get("year", theory.year)),
                    journal=item.get("journal", ""),
                    url=item.get("url", ""),
                    is_open_access=False
                ))
    except Exception as e:
        print(f"CNKI API error: {e}")
    return results

def get_jstor_link(theory: TheoryRef) -> PaperSource:
    url = f"https://www.jstor.org/action/doBasicSearch?Query={quote(theory.theory_name_en + ' ' + theory.theorist_en)}"
    return PaperSource(
        database="JSTOR",
        region="US",
        title=f"在 JSTOR 搜索：{theory.theory_name_en}",
        author=theory.theorist_en,
        year=theory.year,
        url=url
    )

async def fetch_google_scholar_serp(query: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    """
    Fetch Google Scholar results via SerpApi.
    """
    if not SERP_API_KEY:
        return []
        
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 10
    }
    
    results = []
    try:
        response = await client.get(url, params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("organic_results", []):
                # Map to a consistent format for LLM map generation
                results.append({
                    "title": item.get("title", ""),
                    "author": item.get("publication_info", {}).get("summary", "Unknown"),
                    "year": 0, # Year extraction is messy from snippets
                    "url": item.get("link", ""),
                    "abstract": item.get("snippet", ""),
                    "source": "Google Scholar"
                })
    except Exception as e:
        print(f"SerpApi Error: {e}")
    return results

def get_google_scholar_link(theory: TheoryRef) -> PaperSource:
    url = f"https://scholar.google.com/scholar?q={quote(theory.theory_name_en + ' ' + theory.theorist_en)}"
    return PaperSource(
        database="GoogleScholar",
        region="INTL",
        title=f"在 Google Scholar 搜索：{theory.theory_name_en}",
        author=theory.theorist_en,
        year=theory.year,
        url=url
    )

async def search_paper_sources(theory: TheoryRef) -> List[PaperSource]:
    r = redis.from_url(REDIS_URL)
    cache_key = f"cache_sources:{theory.theory_name_en}"
    
    try:
        await r.ping()
        cached_data = await r.get(cache_key)
        if cached_data:
            papers_list = json.loads(cached_data)
            return [PaperSource(**p) for p in papers_list]
    except Exception as e:
        print(f"Redis get error: {e}")
        r = None # Signal that we shouldn't try caching later

    async with httpx.AsyncClient(verify=False) as client:
        # Run API fetchers concurrently
        s2_task = fetch_semantic_scholar(theory, client)
        cr_task = fetch_crossref(theory, client)
        cnki_task = fetch_cnki(theory, client)
        
        # Add SerpApi if available
        query = f"{theory.theory_name_en} {theory.theorist_en}"
        serp_task = fetch_google_scholar_serp(query, client)
        
        api_results = await asyncio.gather(s2_task, cr_task, cnki_task, serp_task, return_exceptions=True)
        
    all_sources = []
    for res in api_results:
        if isinstance(res, list):
            for item in res:
                if isinstance(item, PaperSource):
                    all_sources.append(item)
                elif isinstance(item, dict):
                    # Convert SerpApi dict to PaperSource
                    all_sources.append(PaperSource(
                        database="GoogleScholar",
                        region="INTL",
                        title=item.get("title", "Unknown"),
                        author=item.get("author", "Unknown"),
                        year=theory.year,
                        url=item.get("url", ""),
                        is_open_access=False
                    ))
            
    # Add static links
    all_sources.append(get_jstor_link(theory))
    all_sources.append(get_google_scholar_link(theory))
    
    # Deduplicate by URL or title
    seen_urls = set()
    unique_sources = []
    for s in all_sources:
        if s.url and s.url not in seen_urls:
            unique_sources.append(s)
            seen_urls.add(s.url)
            
    # Sorting logic
    # a. is_open_access=True 的排前面
    # b. citation_count 高的排前面
    # c. 中文单独分组不混排
    cn_sources = [s for s in unique_sources if s.region == "CN"]
    intl_sources = [s for s in unique_sources if s.region != "CN"]
    
    def sort_key(s: PaperSource):
        return (not s.is_open_access, -s.citation_count)
        
    cn_sources.sort(key=sort_key)
    intl_sources.sort(key=sort_key)
    
    # 最终返回：英文最多4条 + 中文最多2条
    final_sources = intl_sources[:4] + cn_sources[:2]
    
    # Cache to Redis (TTL 7 days)
    if r:
        try:
            data_to_cache = [json.loads(p.model_dump_json()) for p in final_sources]
            await r.setex(cache_key, 7 * 24 * 3600, json.dumps(data_to_cache))
        except Exception as e:
            print(f"Redis set error: {e}")
        finally:
            await r.aclose()
        
    return final_sources

async def fetch_paper_sources(job_id: str, shot_id: int, theories: List[TheoryRef]):
    """
    Entry point for analyzer pipeline. Processes all theories for a single shot.
    """
    if not theories:
        return
        
    tasks = [search_paper_sources(t) for t in theories]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    r = redis.from_url(REDIS_URL)
    try:
        await r.ping()
        for i, theory in enumerate(theories):
            res = results[i]
            if isinstance(res, Exception):
                theory.sources_error = str(res)
                theory.sources = []
            else:
                theory.sources = res
            theory.sources_loaded = True
            
            # 推送 sources_ready 事件
            event_data = {
                "event": "sources_ready",
                "shot_id": shot_id,
                "theory_name_en": theory.theory_name_en,
                "sources": [json.loads(p.model_dump_json()) for p in theory.sources]
            }
            event_json = json.dumps(event_data)
            await r.publish(f"channel:{job_id}", event_json)
            # Cache for state replay
            await r.hset(f"status:{job_id}:results", f"sources:{shot_id}:{theory.theory_name_en}", event_json)
    except Exception as e:
        print(f"Redis publish sources error: {e}")
    finally:
        await r.aclose()
