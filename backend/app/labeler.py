from PIL import Image
import numpy as np
from ultralytics import YOLO

MODEL_PATH = 'yolov8n.pt'  # Update with your own weights if available!
model = YOLO(MODEL_PATH)
COCO_NAMES = model.names if hasattr(model, "names") else {i: f"class_{i}" for i in range(1000)}

def label_image(path: str) -> dict:
    img = Image.open(path)
    results = model(img)
    labels = []
    result = results[0]  # Get first result, as only one inference
    boxes = result.boxes
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        conf = box.conf[0].cpu().numpy().item()
        cls = int(box.cls[0].cpu().numpy().item())
        labels.append({
            "type": COCO_NAMES[cls],
            "bbox": [x1, y1, x2, y2],
            "confidence": conf
        })
    arr = np.array(img.convert("RGB")).astype(float)
    r, g, b = arr.mean(axis=(0, 1))
    brightness = float(0.299 * r + 0.587 * g + 0.114 * b)
    return {
        "objects": labels,
        "meta": {
            "brightness": round(brightness, 1),
            "mean_color": [int(r), int(g), int(b)]
        }
    }
