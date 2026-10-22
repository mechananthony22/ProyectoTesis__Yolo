import io
import math
from PIL import Image, ImageEnhance


def transform(data, boxes, recipe):
    if recipe.get("size") not in (640, 800):
        raise ValueError("La resolución debe ser 640 u 800.")
    for key in ("brightness", "contrast"):
        value = float(recipe.get(key, 1))
        if not math.isfinite(value) or not 0.5 <= value <= 1.5:
            raise ValueError("Brillo y contraste deben estar entre 0.5 y 1.5.")
    image = Image.open(io.BytesIO(data)).convert("RGB")
    width, height = image.size
    crop = recipe.get("crop", [0, 0, 1, 1])
    if len(crop) != 4 or not all(math.isfinite(v) and 0 <= v <= 1 for v in crop):
        raise ValueError("Recorte normalizado inválido.")
    left, top, right, bottom = [
        round(v * n) for v, n in zip(crop, [width, height, width, height])
    ]
    if right <= left or bottom <= top:
        raise ValueError("El recorte debe conservar al menos un píxel en cada dimensión.")
    image = image.crop((left, top, right, bottom))
    cw, ch = image.size
    target = recipe["size"]
    scale = min(target / cw, target / ch)
    nw, nh = max(1, round(cw * scale)), max(1, round(ch * scale))
    dx, dy = (target - nw) // 2, (target - nh) // 2
    image = ImageEnhance.Brightness(image).enhance(recipe.get("brightness", 1))
    image = ImageEnhance.Contrast(image).enhance(recipe.get("contrast", 1))
    canvas = Image.new("RGB", (target, target), (255, 255, 255))
    canvas.paste(image.resize((nw, nh), Image.Resampling.LANCZOS), (dx, dy))
    result = []
    for b in boxes:
        x1 = max(left, (b["x"] - b["w"] / 2) * width)
        x2 = min(right, (b["x"] + b["w"] / 2) * width)
        y1 = max(top, (b["y"] - b["h"] / 2) * height)
        y2 = min(bottom, (b["y"] + b["h"] / 2) * height)
        if x2 > x1 and y2 > y1:
            result.append(
                {
                    "class_id": 0,
                    "x": (((x1 + x2) / 2 - left) * nw / cw + dx) / target,
                    "y": (((y1 + y2) / 2 - top) * nh / ch + dy) / target,
                    "w": (x2 - x1) * nw / cw / target,
                    "h": (y2 - y1) * nh / ch / target,
                }
            )
    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue(), result
