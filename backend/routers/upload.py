import os
import uuid
import shutil
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Request, Form
from pydantic import BaseModel
from backend.services.pipeline import run_analysis_pipeline

router = APIRouter()

class UploadResponse(BaseModel):
    job_id: str
    status: str
    ws_url: str

ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "avi"}

@router.post("/upload", response_model=UploadResponse)
async def upload_video(
    request: Request, 
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    locale: str = Form("en-US"),
    film_title: str = Form("Untitled Clip"),
    director: str = Form("Unknown"),
    film_title_en: str = Form(""),
    director_en: str = Form("")
):
    # Validate file extension
    ext = file.filename.split('.')[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    
    # Setup job and temp directories
    job_id = str(uuid.uuid4())
    temp_root = os.path.join(tempfile.gettempdir(), "filmlens")
    job_dir = os.path.join(temp_root, job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    # Save original file
    file_path = os.path.join(job_dir, f"original.{ext}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Construct persistent ws_url
    host = request.headers.get("host", "localhost:8000")
    scheme = "wss" if request.url.scheme == "https" else "ws"
    ws_url = f"{scheme}://{host}/ws/{job_id}"

    # Hand off to async pipeline
    # Note: background_tasks.add_task works with async functions too
    background_tasks.add_task(run_analysis_pipeline, job_id, file_path, locale, film_title, director, film_title_en, director_en)

    return UploadResponse(job_id=job_id, status="processing", ws_url=ws_url)
