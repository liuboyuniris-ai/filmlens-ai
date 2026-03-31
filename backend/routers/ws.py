import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.redis_client import get_redis_client
from backend.services.chat_agent import handle_chat_query

router = APIRouter()

@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    
    # 1. Connection Success
    await websocket.send_text(json.dumps({
        "event": "ws_connected",
        "message": "WebSocket handshaked successfully"
    }))
    
    r = get_redis_client()
    
    # Check if a video already exists for replay
    if os.path.exists(f"static/jobs/{job_id}/video.mp4"):
        await websocket.send_text(json.dumps({
            "event": "video_ready", 
            "video_url": f"/static/jobs/{job_id}/video.mp4"
        }))

    # --- STATE REPLAY ---
    analysis_path = f"static/jobs/{job_id}/analysis.json"
    if os.path.exists(analysis_path):
        print(f"[WebSocket] Loading persistent state from {analysis_path}")
        # Read from file directly
        try:
            with open(analysis_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
                
            # Send shots first so UI can build timeline
            shots = report_data.get("shots", [])
            if shots:
                await websocket.send_text(json.dumps({
                    "event": "shots_detected",
                    "shots": shots
                }))
            
            # Send film context
            context = report_data.get("film_context")
            if context:
                await websocket.send_text(json.dumps({
                    "event": "film_context",
                    "context": context
                }))
            
            # Send research map if it exists separately or inside context
            research_map = report_data.get("research_map")
            if research_map:
                 await websocket.send_text(json.dumps({
                    "event": "research_map_ready",
                    "research_map": research_map
                }))

            # Send analyses
            analyses = report_data.get("analyses", {})
            for shot_id_str, analysis_data in analyses.items():
                await websocket.send_text(json.dumps({
                    "event": "shot_analyzed",
                    "shot_id": int(shot_id_str),
                    "analysis": analysis_data
                }))
                
            await websocket.send_text(json.dumps({"event": "complete"}))
            print(f"[WebSocket] State replay complete for {job_id}")
        except Exception as e:
            print(f"[WebSocket] Error replaying state from file: {e}")
            await websocket.send_text(json.dumps({"event": "error", "message": f"Failed to load analysis file: {str(e)}"}))
    else:
        # Replay Shots from Redis
        cached_shots = await r.get(f"status:{job_id}:shots")
        if cached_shots: await websocket.send_text(cached_shots)
        
        # Replay Film Context from Redis
        cached_context = await r.get(f"status:{job_id}:context")
        if cached_context: await websocket.send_text(cached_context)
        
        # Replay all individual results from Redis
        cached_results = await r.hgetall(f"status:{job_id}:results")
        for result_json in (cached_results or {}).values():
            await websocket.send_text(result_json)
        
        # Replay Completion status
        job_state = await r.hget(f"status:{job_id}", "state")
        if job_state == "complete":
            await websocket.send_text(json.dumps({"event": "complete"}))

    # --- DUPLEX COMMUNICATION ---
    async def listen_to_redis():
        pubsub = r.pubsub()
        await pubsub.subscribe(f"channel:{job_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
                    try:
                        parsed = json.loads(message["data"])
                        if parsed.get("event") == "complete": break
                    except: pass
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()

    listener_task = asyncio.create_task(listen_to_redis())

    try:
        while True:
            client_msg = await websocket.receive_text()
            try:
                data = json.loads(client_msg)
                if data.get("event") == "chat_request":
                    asyncio.create_task(handle_chat_query(job_id, data.get("shot_id"), data.get("question")))
                elif data.get("event") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except json.JSONDecodeError: pass
    except WebSocketDisconnect: pass
    finally:
        listener_task.cancel()
        try:
            await websocket.close()
        except: pass
