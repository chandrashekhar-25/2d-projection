import os
import cv2
from PIL import Image
import io
import base64


def extract_frames(video_path: str, out_dir: str, interval_seconds: float = 1.0, max_frames: int = 20):
    """Extract frames from video every `interval_seconds` seconds up to `max_frames`.
    Saves JPEG files into out_dir and returns list of file paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_interval = max(1, int(round(fps * interval_seconds)))

    saved = []
    frame_idx = 0
    saved_count = 0
    while saved_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            out_path = os.path.join(out_dir, f"frame_{saved_count:04d}.jpg")
            # encode as JPEG
            cv2.imwrite(out_path, frame)
            saved.append(out_path)
            saved_count += 1
        frame_idx += 1

    cap.release()
    return saved


def encode_image_base64(path: str, resize_to: tuple | None = (640, 360)) -> str:
    img = Image.open(path).convert("RGB")
    if resize_to:
        img = img.copy()
        img.thumbnail(resize_to)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"
