from PIL import Image
import numpy as np


def label_image(path: str) -> dict:
    """A lightweight placeholder labeler.

    Returns a dictionary with a textual label (dominant color), a "confidence",
    and a brightness score. Replace with real ML inference as needed.
    """
    img = Image.open(path).convert("RGB")
    # downscale to speed up
    small = img.resize((100, 100))
    arr = np.array(small).astype(float)
    # mean color
    mean_color = arr.mean(axis=(0, 1))
    r, g, b = mean_color

    # basic dominant color labeling
    channels = {'red': r, 'green': g, 'blue': b}
    dominant = max(channels, key=channels.get)
    total = r + g + b
    confidence = float(channels[dominant] / total) if total > 0 else 0.0

    # brightness (0-255)
    brightness = float(0.299 * r + 0.587 * g + 0.114 * b)

    return {
        'label': dominant,
        'confidence': round(confidence, 3),
        'brightness': round(brightness, 1),
        'mean_color': [int(r), int(g), int(b)]
    }
