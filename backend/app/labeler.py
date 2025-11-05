from PIL import Image
import numpy as np
import cv2
from ultralytics import YOLO
import mediapipe as mp

# YOLOv8 Segmentation Model
MODEL_PATH = 'yolov8n-seg.pt'  # Use your custom trained weights if available
model = YOLO(MODEL_PATH)
YOLO_CLASSES = model.names if hasattr(model, "names") else {i: f"class_{i}" for i in range(1000)}

mp_hands = mp.solutions.hands
mp_face = mp.solutions.face_detection

def detect_color(region, image):
    x1, y1, x2, y2 = map(int, region)
    subimg = image.crop((x1, y1, x2, y2)).convert("RGB")
    arr = np.array(subimg)
    mean_color = arr.mean(axis=(0, 1))
    r, g, b = mean_color
    if r > g and r > b:
        return "red"
    elif g > r and g > b:
        return "green"
    elif b > r and b > g:
        return "blue"
    else:
        return "other"

def detect_blur(image):
    img_gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    variance = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    threshold = 100.0
    blurred = bool(variance < threshold)  # explicitly cast to bool
    return blurred, variance

def process_yolo_objects(yolo_result, pil_img):
    objects = []
    for box in yolo_result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
        conf = box.conf[0].cpu().numpy().item()
        cls = int(box.cls[0].cpu().numpy().item())
        class_name = YOLO_CLASSES.get(cls, f"class_{cls}")
        color = detect_color([x1, y1, x2, y2], pil_img)
        mask = None
        if hasattr(yolo_result, "masks") and yolo_result.masks is not None:
            mask_data = yolo_result.masks.data.cpu().numpy()
            if mask_data.shape[0] > 0:
                mask = mask_data[0].tolist()
        objects.append({
            "type": class_name,
            "bbox": [x1, y1, x2, y2],
            "confidence": conf,
            "attributes": {"color": color},
            "mask": mask
        })
    return objects

def process_hands(np_img, pil_img):
    gesture_regions = []
    hand_objs = []
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
                hand_objs.append({
                    "type": "hand",
                    "bbox": [bx1, by1, bx2, by2],
                    "confidence": 1.0,
                    "attributes": {},
                    "mask": None
                })
    return gesture_regions, hand_objs

def process_faces(np_img, pil_img):
    face_objs = []
    with mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5) as face:
        results = face.process(np_img)
        if results.detections:
            for det in results.detections:
                box = det.location_data.relative_bounding_box
                bx1 = box.xmin * pil_img.width
                by1 = box.ymin * pil_img.height
                bx2 = (box.xmin + box.width) * pil_img.width
                by2 = (box.ymin + box.height) * pil_img.height
                cropped_face = pil_img.crop((bx1, by1, bx2, by2))
                blurred, blur_metric = detect_blur(cropped_face)
                face_objs.append({
                    "type": "face",
                    "bbox": [bx1, by1, bx2, by2],
                    "confidence": det.score[0],
                    "attributes": {
                        "blurred": bool(blurred),
                        "blur_metric": blur_metric
                    },
                    "mask": None
                })
    return face_objs

def detect_interactions(objects):
    hand_objects = [obj for obj in objects if obj["type"] == "hand"]
    interactable_objects = [obj for obj in objects if obj["type"] not in ["hand", "face", "background"]]
    interactions = []
    for hand_obj in hand_objects:
        h_box = hand_obj["bbox"]
        for target_obj in interactable_objects:
            t_box = target_obj["bbox"]
            overlap_area = max(0, min(h_box[2], t_box[2]) - max(h_box[0], t_box[0])) * max(0, min(h_box[3], t_box[3]) - max(h_box[1], t_box[1]))
            if overlap_area > 0:
                interactions.append({
                    "relation": f"hand_touches_{target_obj['type']}",
                    "hand_bbox": h_box,
                    "target_bbox": t_box
                })
    return interactions

def compute_global_meta(pil_img, frame_num):
    arr = np.array(pil_img).astype(float)
    r, g, b = arr.mean(axis=(0, 1))
    brightness = float(0.299 * r + 0.587 * g + 0.114 * b)
    meta = {
        "brightness": round(brightness, 1),
        "mean_color": [int(r), int(g), int(b)]
    }
    if frame_num is not None:
        meta["frame_number"] = frame_num
    return meta

def label_image(path: str, frame_num: int = None) -> dict:
    pil_img = Image.open(path).convert("RGB")
    np_img = np.array(pil_img)
    yolo_results = model(pil_img)
    yolo_result = yolo_results[0]

    objects = process_yolo_objects(yolo_result, pil_img)
    gesture_regions, hand_objs = process_hands(np_img, pil_img)
    face_objs = process_faces(np_img, pil_img)
    objects += hand_objs + face_objs

    interactions = detect_interactions(objects)
    meta = compute_global_meta(pil_img, frame_num)

    return {
        "objects": objects,
        "gesture_regions": gesture_regions,
        "interactions": interactions,
        "meta": meta
    }

# Example usage:
# result = label_image('image.jpg', frame_num=1)
