from PIL import Image
import os

def export_yolo(labels_per_image, output_dir, class_map):
    """
    labels_per_image: list of dicts,
        each contains:
            {
                'filename': 'frame_0000.jpg',
                'label': {
                    'objects': [ {'type': 'hand', 'bbox': [x1, y1, x2, y2], ...}, ... ],
                    ...
                }
            }
    output_dir: where to write YOLO .txt files
    class_map: dict, e.g. {'hand': 0, 'skeleton': 1, ...}
    """
    os.makedirs(output_dir, exist_ok=True)
    for item in labels_per_image:
        img_path = item["filename"]
        txt_path = os.path.join(output_dir, os.path.splitext(os.path.basename(img_path))[0] + ".txt")
        img = Image.open(img_path)
        img_w, img_h = img.size
        with open(txt_path, 'w') as f:
            for obj in item["label"]["objects"]:
                class_name = obj["type"]
                cls_id = class_map.get(class_name, -1)
                if cls_id < 0:
                    continue
                x1, y1, x2, y2 = obj['bbox']
                cx = (x1 + x2) / 2.0 / img_w
                cy = (y1 + y2) / 2.0 / img_h
                w = (x2 - x1) / img_w
                h = (y2 - y1) / img_h
                f.write(f"{cls_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
