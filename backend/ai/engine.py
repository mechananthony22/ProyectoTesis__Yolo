"""No imports of Django: trusted weights and explicit device supplied by caller."""

from functools import lru_cache
from time import perf_counter
import io
from PIL import Image, ImageDraw


@lru_cache(maxsize=2)
def load_model(path, digest):
    from ultralytics import YOLO

    return YOLO(path)


def predict(path, digest, image_path, confidence, device):
    model = load_model(path, digest)
    start = perf_counter()
    result = model.predict(
        source=str(image_path), conf=confidence, device=device, verbose=False
    )[0]
    elapsed = (perf_counter() - start) * 1000
    boxes = []
    for b in result.boxes:
        if int(b.cls[0]) != 0:
            raise ValueError("El modelo debe tener exclusivamente la clase rona (0).")
        x, y, w, h = b.xywhn[0].tolist()
        boxes.append(
            {
                "class_id": 0,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "confidence": float(b.conf[0]),
            }
        )
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size
    for b in boxes:
        rect = [
            (b["x"] - b["w"] / 2) * width,
            (b["y"] - b["h"] / 2) * height,
            (b["x"] + b["w"] / 2) * width,
            (b["y"] + b["h"] / 2) * height,
        ]
        draw.rectangle(rect, outline="#e44d40", width=max(2, width // 300))
        draw.text(
            (rect[0] + 4, rect[1] + 4), f"rona {b['confidence']:.2f}", fill="#e44d40"
        )
    out = io.BytesIO()
    img.save(out, format="PNG")
    return boxes, elapsed, out.getvalue()
