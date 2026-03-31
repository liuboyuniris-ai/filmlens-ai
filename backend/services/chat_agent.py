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
        title = film_context.get("film_title", "Untitled")
        director = film_context.get("director", "Unknown")
        summary = film_context.get("summary", "No summary available.")
        
        system_prompt = f"""You are a senior film scholar and cinematic analysis expert. The user is watching the film "{title}" (Directed by: {director}).
You have already conducted a pre-analysis of the entire film, and the user is now asking follow-up questions about a specific shot or the entire film.

Film Macro Context:
{summary}

"""
        if shot_analysis:
            theory = shot_analysis.get("theoretical_connections", [])
            technique = shot_analysis.get("primary_technique", "Unknown")
            system_prompt += f"""Current focus: Shot {shot_id}
Primary technique: {technique}
Theoretical connections: {json.dumps(theory, ensure_ascii=False)}
Narrative function: {shot_analysis.get("narrative_function", "Unknown")}

"""

        system_prompt += """Based on the context above, provide professional, profound, and friendly answers to the user's questions. If the question involves film theory, cite academic concepts; if it involves visual analysis, explain the director's potential intentions.

Requirements:
- Ensure academic depth but keep it concise (approx. 150-300 words).
- Use English for all responses.
- Maintain a tone consistent with professional cinematic analysis.
"""

        # 3. Call Gemini
        if not native_client:
            await r.publish(f"channel:{job_id}", json.dumps({
                "event": "chat_response",
                "answer": "❌ Sorry, the AI chat service is not configured with an API Key."
            }, ensure_ascii=False))
            return

        print(f"[Chat {job_id}] Query: {question}")
        response = await asyncio.to_thread(
            native_client.models.generate_content,
            model=LLM_MODEL,
            contents=[system_prompt, f"User Question: {question}"],
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
                "answer": f"⚠️ An error occurred while thinking ({str(e)}). Please try again later."
            }))
        except: pass
