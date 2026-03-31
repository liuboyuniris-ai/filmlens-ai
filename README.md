# FilmLens AI 🎬 (Academic-Grade Cinema Analysis Engine)

**FilmLens AI** is a professional cinematic analysis tool designed for film scholars, students, and critics. It combines the latest **Google Gemini Multimodal LLM** with **Academic Research Mapping** to automatically segment feature-length films into individual shots, providing detailed audiovisual analysis and theoretical context.

---

## 🔥 Core Features

- **High-Efficiency Feature Support**: Deeply optimized for 2h+ movies, supporting concurrent batch analysis for long films.
- **AI Audiovisual Analysis**: Automatically detects Shot Scale, Camera Movement, Angle, Lighting, and Director's Auteur Style.
- **Academic Research Mapping**: Real-time integration with **Semantic Scholar**, **SerpApi**, and other academic databases to match film theory literature automatically.
- **Persistent Analysis Reports**: All analysis results are saved as `analysis.json`, supporting session reloading to avoid redundant API costs.
- **Premium Design**: A sophisticated multi-pane workspace with synchronized timeline controls and real-time AI theoretical chat.

---

## 🛡️ Privacy & Security (Important for Public Repos)

1.  **API Key Security**: This project is configured with `.gitignore` to ignore `.env` files. **NEVER push your real `.env` file to GitHub.**
2.  **Large File Filtering**: Since movie files are massive (> 1GB), the project automatically ignores everything under `/static/jobs/` (videos, frames, and analysis cache) to keep the repository clean and comply with GitHub's file size limits.

---

## 🛠️ Prerequisites

- **Python 3.10+** (Backend API)
- **Node.js 18+** (Next.js Frontend)
- **Redis** (Critical: Used for WebSocket event pushing and data caching)
- **FFmpeg** (**Required**: Used for video transcoding and frame extraction)

---

## 📦 Installation & Setup

### 1. Configuration
Create a `.env` file in the root directory:
```bash
# Google Gemini API Key (Required)
LLM_API_KEY="AIza..."
LLM_MODEL="gemini-2.0-flash"

# Redis Configuration
REDIS_URL="redis://localhost:6379"

# Academic Search APIs (Optional)
SEMANTIC_SCHOLAR_API_KEY="..."
SERPAPI_API_KEY="..."
```

### 2. Backend Installation
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Installation
```bash
npm install
```

---

## 🏃 Running the Application

1.  **Start Redis**: Ensure your Redis service is running.
2.  **Start Backend**: `python -m backend.main` (Default: port 8000)
3.  **Start Frontend**: `npm run dev` (Default: port 3000)

---

## 💡 Pro Tip: Importing Large Movies (Import Hack)

If your machine lacks the performance to transcode 2-hour movies in real-time, follow these steps to import pre-processed data:

1.  After processing on a high-performance machine, copy the entire `jobs/{uuid}/` folder to your local `static/jobs/` directory.
2.  Ensure the folder contains `video.mp4`, `analysis.json`, and the `frames/` directory.
3.  **DO NOT re-upload** in the UI. Simply browse to: `http://localhost:3000/analyze/{uuid}`.
4.  The system will detect the existing data and load the full analysis **instantly**.

---

## 📜 License
MIT License. Empowering digital humanities and film studies!
