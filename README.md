# 2d-projection

Minimal project: frontend + backend (FastAPI) for uploading a video, extracting screenshots, labeling each screenshot, and returning a JSON response with labels and screenshot info.

Quick start (Windows / PowerShell):

1. Backend: install and run

```powershell
cd 2d-projection\backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. Frontend: open `2d-projection/frontend/index.html` in your browser (or serve it) and upload a video.

Notes:
- Frame extraction uses OpenCV.
- The labeler is a lightweight placeholder that returns dominant color and brightness as labels. Replace with a ML model if needed.
