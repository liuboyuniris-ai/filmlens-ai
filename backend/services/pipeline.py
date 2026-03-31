import os
import json
import asyncio
import traceback
from backend.services.shot_detector import detect_shots
from backend.services.analyzer import analyze_all_shots, generate_film_context, generate_research_map, publish_event
from backend.models import FilmContext, JobStatus
from backend.redis_client import get_redis_client

async def transcode_to_mp4_async(input_path: str, output_path: str):
    """
    Transcode video to web-compatible MP4 using FFmpeg asynchronously.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-strict", "-2",
        "-movflags", "+faststart",
        output_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await process.wait()
    return process.returncode == 0

async def run_analysis_pipeline(
    job_id: str, 
    video_path: str, 
    locale: str = "zh-CN", 
    film_title: str = "未命名片段", 
    director: str = "未知",
    film_title_en: str = "",
    director_en: str = ""
):
    """
    The main analysis pipeline, now fully async.
    """
    r = get_redis_client()
    try:
        # Check if already complete on disk
        static_job_dir = f"static/jobs/{job_id}"
        analysis_path = os.path.join(static_job_dir, "analysis.json")
        if os.path.exists(analysis_path):
            print(f"[Pipeline {job_id}] Found existing analysis.json, skipping processing.")
            await r.hset(f"status:{job_id}", "state", "complete")
            await publish_event(job_id, {
                "event": "complete",
                "job_id": job_id,
                "message": "检测到已有分析结果，已自动加载。"
            })
            return

        print(f"[Pipeline {job_id}] Starting...")
        
        # 1. Initial State Setup
        initial_context = FilmContext(
            job_id=job_id,
            film_title=film_title,
            director=director,
            production_year=2024,
            country_of_production="未知",
            political="等待全片汇总...",
            economic="等待全片汇总...",
            cultural="等待全片汇总...",
            gender_sexuality="等待全片汇总...",
            postcolonial="等待全片汇总...",
            technological="等待全片汇总...",
            auteur_biography="等待全片汇总...",
            summary="正在分析镜头以生成摘要...",
            search_keywords_en=[film_title_en, director_en] if film_title_en else [],
            search_keywords_cn=[film_title, director]
        )
        # Store EN fields in FilmContext if needed, 
        # but for now we'll just use them in searches.
        # Let's add them to the model to be safe.
        
        # Seed cache
        await r.setex(f"status:{job_id}:context", 3600 * 24, json.dumps({
            "event": "film_context", 
            "context": initial_context.model_dump()
        }, ensure_ascii=False))
        
        await publish_event(job_id, {
            "event": "pipeline_started",
            "message": f"引擎流水线已启动: 《{film_title}》"
        })

        # 2. Transcode
        static_job_dir = f"static/jobs/{job_id}"
        os.makedirs(static_job_dir, exist_ok=True)
        static_video_path = os.path.join(static_job_dir, "video.mp4")
        
        print(f"[Pipeline {job_id}] Transcoding...")
        success = await transcode_to_mp4_async(video_path, static_video_path)
        if not success:
            print(f"[Pipeline {job_id}] Transcoding failed!")
            # Fallback: copy original if transcoding fails, though not ideal
            import shutil
            shutil.copy2(video_path, static_video_path)

        await publish_event(job_id, {
            "event": "video_ready",
            "video_url": f"/static/jobs/{job_id}/video.mp4"
        })

        # 3. Shot Detection (Offload sync to thread)
        print(f"[Pipeline {job_id}] Detecting shots...")
        shots = await asyncio.to_thread(detect_shots, job_id, static_video_path)
        
        shots_payload = {
            "event": "shots_detected",
            "shots": [s.model_dump() for s in shots]
        }
        await r.setex(f"status:{job_id}:shots", 3600, json.dumps(shots_payload, ensure_ascii=False))
        await publish_event(job_id, shots_payload)

        # 4. Analysis
        await r.hset(f"status:{job_id}", "state", "analyzing")
        job = JobStatus(
            job_id=job_id,
            status="analyzing",
            film_context=initial_context,
            total_shots=len(shots),
            shots=shots
        )
        
        print(f"[Pipeline {job_id}] Analyzing {len(shots)} shots...")
        results = await analyze_all_shots(job_id, shots, locale, job)
        
        # 5. Full Context Generation
        print(f"[Pipeline {job_id}] Generating macro context...")
        valid_results = [r for r in results if r]
        film_context = await generate_film_context(job_id, valid_results, locale, initial_context)
        
        # 6. Global Research Mapping
        print(f"[Pipeline {job_id}] Generating global research map...")
        # Use EN fields if provided, otherwise fallback to CN
        search_title = film_title_en if film_title_en else film_title
        search_director = director_en if director_en else director
        research_map_data = await generate_research_map(job_id, search_title, search_director)
        from backend.models import FilmResearchMap
        film_context.research_map = FilmResearchMap(**research_map_data)
        
        # 7. Save Final Report
        report = {
            "job_id": job_id,
            "total_shots": len(shots),
            "analyzed_shots": len(valid_results),
            "film_context": film_context.model_dump(),
            "shots": [s.model_dump() for s in shots],
            "analyses": {str(r.shot_id): r.model_dump() for r in valid_results}
        }
        report_path = os.path.join(static_job_dir, "analysis.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        await r.hset(f"status:{job_id}", "state", "complete")
        await publish_event(job_id, {
            "event": "complete", # Use 'complete' consistently
            "job_id": job_id,
            "message": "影片分析与学术资源地图构建已完成。"
        })
        print(f"[Pipeline {job_id}] Done.")

    except Exception as e:
        print(f"=== PIPELINE ERROR {job_id} ===")
        traceback.print_exc()
        await publish_event(job_id, {
            "event": "error",
            "message": f"流水线运行出错: {str(e)}"
        })
