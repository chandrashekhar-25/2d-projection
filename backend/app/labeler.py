from PIL import Image
import numpy as np
from ultralytics import YOLO
import mediapipe as mp

# Load YOLOv8 model
MODEL_PATH = 'yolov8n.pt'  # Use your custom weights if available
model = YOLO(MODEL_PATH)
YOLO_CLASSES = model.names if hasattr(model, "names") else {i: f"class_{i}" for i in range(1000)}

# Mediapipe hands
mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection

# Example: custom attribute heuristics
def detect_color(region, image):
    # region: [x1, y1, x2, y2]
    x1, y1, x2, y2 = map(int, region)
    subimg = image.crop((x1, y1, x2, y2)).convert("RGB")
    arr = np.array(subimg)
    mean_color = arr.mean(axis=(0, 1))
    r, g, b = mean_color
    # Simplistic label
    if r > g and r > b:
        return "red"
    elif g > r and g > b:
        return "green"
    elif b > r and b > g:
        return "blue"
    else:
        return "other"

def label_image(path: str, frame_num: int = None) -> dict:
    pil_img = Image.open(path)
    np_img = np.array(pil_img)

    # --- YOLOv8 detection ---
    yolo_results = model(pil_img)
    yolo_result = yolo_results[0]
    objects = []
    for box in yolo_result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        conf = box.conf[0].cpu().numpy().item()
        cls = int(box.cls[0].cpu().numpy().item())
        class_name = YOLO_CLASSES[cls]
        # Attribute example
        color = detect_color([x1, y1, x2, y2], pil_img)
        mask = None  # Placeholder for mask/polygon (requires instance segmentation)
        objects.append({
            "type": class_name,
            "bbox": [x1, y1, x2, y2],
            "confidence": conf,
            "attributes": {
                "color": color
            },
            "mask": mask
        })

    # --- Mediapipe: hands/faces for gesture/interactions ---
    gesture_regions = []
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2) as hands:
        results = hands.process(np_img)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                x_list = [lm.x * pil_img.width for lm in hand_landmarks.landmark]
                y_list = [lm.y * pil_img.height for lm in hand_landmarks.landmark]
                bx1, by1, bx2, by2 = min(x_list), min(y_list), max(x_list), max(y_list)
                gesture_regions.append({
                    "region": [bx1, by1, bx2, by2],
                    "class": "hand",
                    "landmarks": [{"x": x, "y": y} for x, y in zip(x_list, y_list)]
                })
                objects.append({
                    "type": "hand",
                    "bbox": [bx1, by1, bx2, by2],
                    "confidence": 1.0,
                    "attributes": {},
                    "mask": None
                })
    # Detect faces for attributes: blurred, etc.
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face:
        results = face.process(np_img)
        if results.detections:
            for det in results.detections:
                box = det.location_data.relative_bounding_box
                bx1 = box.xmin * pil_img.width
                by1 = box.ymin * pil_img.height
                bx2 = (box.xmin + box.width) * pil_img.width
                by2 = (box.ymin + box.height) * pil_img.height
                is_blurred = False  # implement blur detection as needed
                objects.append({
                    "type": "face",
                    "bbox": [bx1, by1, bx2, by2],
                    "confidence": det.score[0],
                    "attributes": {"blurred": is_blurred},
                    "mask": None
                })

    # --- Meta and relationships ---
    arr = np.array(pil_img.convert("RGB")).astype(float)
    r, g, b = arr.mean(axis=(0, 1))
    brightness = float(0.299 * r + 0.587 * g + 0.114 * b)
    mean_color = [int(r), int(g), int(b)]

    # Example interaction regions/relationships (hand touching skeleton)
    interactions = []
    for obj in objects:
        if obj["type"] == "hand":
            for target in objects:
                if target["type"] == "skeleton":
                    # Check overlap or proximity (rough example)
                    h_box = obj["bbox"]
                    s_box = target["bbox"]
                    overlap = (
                        max(0, min(h_box[2], s_box[2]) - max(h_box[0], s_box[0])) *
                        max(0, min(h_box[3], s_box[3]) - max(h_box[1], s_box[1]))
                    )
                    if overlap > 0:
                        interactions.append({
                            "relation": "hand_touches_skeleton",
                            "hand_bbox": h_box,
                            "skeleton_bbox": s_box
                        })

    temporal = {"frame_number": frame_num} if frame_num is not None else {}

    return {
        "objects": objects,
        "gesture_regions": gesture_regions,
        "interactions": interactions,
        "meta": {
            "brightness": round(brightness, 1),
            "mean_color": mean_color,
            **temporal
        }
    }
