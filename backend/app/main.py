import os
import shutil
import tempfile
import uuid
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import aiofiles

from . import utils, labeler

app = FastAPI(title="2d-projection: video -> screenshots + labels")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/process-video")
async def process_video(file: UploadFile = File(...), interval_seconds: float = 1.0, max_frames: int = 20):
    """Accepts a video file, extracts frames, labels each frame, and returns JSON.

    Returns:
    {
      "video_filename": "...",
      "frames": [ {"filename": "...", "data": "data:image...", "label": {...}}, ... ]
    }
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # create temp working dir
    work_dir = tempfile.mkdtemp(prefix="2dproj_")
    try:
        video_path = os.path.join(work_dir, f"upload_{uuid.uuid4().hex}_{file.filename}")
        content = await file.read()
        # write file asynchronously
        async with aiofiles.open(video_path, "wb") as f:
            await f.write(content)

        frames_dir = os.path.join(work_dir, "frames")
        frames = utils.extract_frames(video_path, frames_dir, interval_seconds=interval_seconds, max_frames=max_frames)

        response_frames = []
        for p in frames:
            lbl = labeler.label_image(p)
            data_url = utils.encode_image_base64(p)
            response_frames.append({
                "filename": os.path.basename(p),
                "data": data_url,
                "label": lbl,
            })

        return JSONResponse({
            "video_filename": file.filename,
            "frames": response_frames,
            "count": len(response_frames),
        })
    finally:
        # keep the uploaded file and frames while debugging? remove for cleanup
        # remove temp working directory to avoid disk accumulation
        try:
            shutil.rmtree(work_dir)
        except Exception:
            pass
