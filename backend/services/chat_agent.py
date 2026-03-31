import asyncio
import json
import os
from google import genai
from google.genai import types
from backend.redis_client import get_redis_client

# Load API key and model
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash")

# Initialize native client
native_client = None
if LLM_API_KEY and LLM_API_KEY.startswith("AIza"):
    native_client = genai.Client(api_key=LLM_API_KEY)

async def handle_chat_query(job_id: str, shot_id: int | None, question: str):
    """
    Background worker for handling user follow-up questions.
    Uses shared Redis connection for consistent state.
    """
    r = get_redis_client()
    try:
        # 1. Gather context from Redis or fallback to analysis.json
        context_raw = await r.get(f"status:{job_id}:context")
        film_context_data = json.loads(context_raw) if context_raw else {}
        film_context = film_context_data.get("context", {})
        
        shot_analysis = {}
        if shot_id is not None:
            shot_raw = await r.hget(f"status:{job_id}:results", f"shot:{shot_id}")
            if shot_raw:
                shot_data = json.loads(shot_raw)
                shot_analysis = shot_data.get("analysis", {})

        # Fallback to analysis.json if Redis data is missing
        if not film_context or (shot_id is not None and not shot_analysis):
            analysis_path = f"static/jobs/{job_id}/analysis.json"
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    report_data = json.load(f)
                    if not film_context:
                        film_context = report_data.get("film_context", {})
                    if shot_id is not None and not shot_analysis:
                        shot_analysis = report_data.get("analyses", {}).get(str(shot_id), {})

        # 2. Build the chat prompt
        title = film_context.get("film_title", "未命名片段")
        director = film_context.get("director", "未知")
        summary = film_context.get("summary", "暂无总结")
        
        system_prompt = f"""你是一个资深的电影学者和拉片专家。用户正在观看影片《{title}》（导演：{director}）。
你已经对全片进行了视听预分析，当前用户对某个特定镜头或全片提出了深度追问。

影片宏观背景:
{summary}

"""
        if shot_analysis:
            theory = shot_analysis.get("theoretical_connections", [])
            technique = shot_analysis.get("primary_technique", "未知")
            system_prompt += f"""当前追问聚焦镜头: 第 {shot_id} 镜
主要技法: {technique}
已有关联理论: {json.dumps(theory, ensure_ascii=False)}
叙事功能: {shot_analysis.get("narrative_function", "未知")}

"""

        system_prompt += """请基于以上背景，专业、深刻且友好地回答用户的问题。如果问题涉及电影理论，请引用学术概念；如果涉及视觉分析，请解释导演可能的意图。
回答要求：
- 语言简练但也保证学术深度（约 150-300 字）
- 使用与系统一致的语言（中文）
- 保持专业电影拉片的基调
"""

        # 3. Call Gemini
        if not native_client:
            await r.publish(f"channel:{job_id}", json.dumps({
                "event": "chat_response",
                "answer": "❌ 抱歉，AI 聊天服务尚未配置 API Key。"
            }, ensure_ascii=False))
            return

        print(f"[Chat {job_id}] Query: {question}")
        response = await asyncio.to_thread(
            native_client.models.generate_content,
            model=LLM_MODEL,
            contents=[system_prompt, f"用户提问：{question}"],
            config=types.GenerateContentConfig(temperature=0.7)
        )
        answer = response.text
        
        # 4. Return result via Redis Pub/Sub
        await r.publish(f"channel:{job_id}", json.dumps({
            "event": "chat_response",
            "answer": answer,
            "ref_shot_id": shot_id
        }, ensure_ascii=False))

    except Exception as e:
        print(f"[Chat Error {job_id}] {e}")
        try:
            await r.publish(f"channel:{job_id}", json.dumps({
                "event": "chat_response",
                "answer": f"⚠️ 在思考时出了点小差错 ({str(e)})，请稍后再试。"
            }))
        except: pass
