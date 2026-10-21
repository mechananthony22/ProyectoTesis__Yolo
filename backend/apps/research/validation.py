import hashlib
import io
import math
import warnings
from pathlib import Path, PurePosixPath
from PIL import Image, ImageOps, ImageStat, ImageFilter, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

Image.MAX_IMAGE_PIXELS = 25_000_000
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def check_boxes(boxes):
    if not isinstance(boxes, list) or len(boxes) > 1000:
        raise ValidationError(
            "Las anotaciones deben ser una lista de hasta 1000 cajas."
        )
    clean = []
    for box in boxes:
        try:
            if box.get("class_id", 0) != 0:
                raise ValueError()
            x, y, w, h = [float(box[k]) for k in ("x", "y", "w", "h")]
            if (
                not all(math.isfinite(v) for v in [x, y, w, h])
                or w <= 0
                or h <= 0
                or x - w / 2 < -1e-8
                or y - h / 2 < -1e-8
                or x + w / 2 > 1 + 1e-8
                or y + h / 2 > 1 + 1e-8
            ):
                raise ValueError()
            clean.append({"class_id": 0, "x": x, "y": y, "w": w, "h": h})
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ValidationError(
                "Caja inválida: usa clase 0 y coordenadas normalizadas dentro de la imagen."
            )
    return clean


def parse_yolo(text):
    boxes = []
    for line in text.splitlines():
        if not line.strip():
            continue
        values = line.split()
        if len(values) != 5 or values[0] != "0":
            raise ValidationError(
                "Etiqueta YOLO inválida. Se espera: 0 x_center y_center width height."
            )
        try:
            boxes.append(
                dict(
                    zip(
                        ["class_id", "x", "y", "w", "h"],
                        [0] + [float(v) for v in values[1:]],
                    )
                )
            )
        except ValueError:
            raise ValidationError("Coordenadas YOLO no numéricas.")
    return check_boxes(boxes)


def inspect_image(data, name):
    if (
        Path(name).suffix.lower() not in ALLOWED_EXTENSIONS
        or len(data) > 20 * 1024 * 1024
    ):
        raise ValidationError("Usa JPG, PNG o WEBP de hasta 20 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as img:
                img.verify()
            with Image.open(io.BytesIO(data)) as img:
                if img.getexif().get(274, 1) != 1:
                    raise ValidationError(
                        "La imagen contiene rotación EXIF. Normaliza la orientación y sus etiquetas antes de importar."
                    )
                if getattr(img, "n_frames", 1) != 1:
                    raise ValidationError("No se admiten imágenes animadas.")
                # Preserve raw pixel coordinates to match existing YOLO labels.
                img = img.convert("RGB")
                width, height = img.size
                gray = ImageOps.grayscale(img)
                tiny = gray.resize((9, 8))
                pix = list(tiny.getdata())
                bits = "".join(
                    "1" if pix[y * 9 + x] > pix[y * 9 + x + 1] else "0"
                    for y in range(8)
                    for x in range(8)
                )
                brightness = ImageStat.Stat(gray).mean[0]
                edges = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES)).var[0]
                return {
                    "width": width,
                    "height": height,
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "perceptual_hash": f"{int(bits, 2):016x}",
                    "quality": {
                        "brightness": round(brightness, 2),
                        "edge_variance": round(edges, 2),
                        "dark_warning": brightness < 35,
                        "blur_warning": edges < 50,
                    },
                }
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise ValidationError("Archivo corrupto o imagen demasiado grande.")


def safe_zip_entries(archive):
    entries = archive.infolist()
    if len(entries) > 5000:
        raise ValidationError("ZIP limitado a 5000 entradas.")
    total = 0
    seen = set()
    for info in entries:
        path = PurePosixPath(info.filename.replace("\\", "/"))
        if (
            path.is_absolute()
            or ".." in path.parts
            or ":" in str(path)
            or ((info.external_attr >> 16) & 0o170000) == 0o120000
        ):
            raise ValidationError("ZIP contiene rutas inseguras o enlaces.")
        if str(path) in seen:
            raise ValidationError("ZIP contiene rutas duplicadas.")
        seen.add(str(path))
        total += info.file_size
        if (
            total > 250 * 1024 * 1024
            or info.file_size > 20 * 1024 * 1024
            or info.file_size > max(1, info.compress_size) * 200
        ):
            raise ValidationError("ZIP excede límites de tamaño o compresión.")
    return entries
