import os
from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import upload, ws
import mimetypes

# Ensure .mp4 is correctly recognized
mimetypes.add_type('video/mp4', '.mp4')

app = FastAPI(title="FilmLens AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for keyframes with CORS support
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        except Exception:
            raise

os.makedirs("static/jobs", exist_ok=True)
app.mount("/static", CORSStaticFiles(directory="static"), name="static")

# Include routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(ws.router, tags=["websocket"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
