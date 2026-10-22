"""YOLOv8 training adapter. No Django imports; artifacts live in caller-owned storage."""

import hashlib
import math
import platform
import os
import subprocess
import logging
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from time import perf_counter

ALLOWED_BASES = ("yolov8n.pt", "yolov8s.pt")
PARAMETERS = {
    "epochs",
    "batch",
    "imgsz",
    "lr0",
    "optimizer",
    "weight_decay",
    "patience",
    "seed",
    "fliplr",
    "degrees",
    "hsv_v",
}


def finite_metrics(values):
    """Undefined metrics are NULL, never invented zeros or invalid JSON NaNs."""
    output = {}
    for key, value in values.items():
        try:
            number = float(value)
            output[str(key)] = number if math.isfinite(number) else None
        except (TypeError, ValueError, OverflowError):
            output[str(key)] = None
    return output


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def environment(device):
    import torch

    versions = {}
    for package in [
        "torch",
        "torchvision",
        "ultralytics-opencv-headless",
        "opencv-python-headless",
        "numpy",
        "pillow",
    ]:
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    try:
        root = Path(__file__).resolve().parents[2]
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            .decode()
            .strip()
        )
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
        )
    except (OSError, subprocess.SubprocessError):
        commit, dirty = None, None
    return {
        "source_commit": os.getenv("BUILD_COMMIT") or commit,
        "source_dirty": dirty,
        "adapter_sha256": file_sha256(__file__),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
        "device": device,
        "cpu": platform.processor(),
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


def train_model(
    *,
    data_yaml,
    architecture,
    weights_dir,
    output_dir,
    parameters,
    device,
    on_epoch,
    on_start,
    model_factory=None,
):
    if str(device) != "cpu" and not str(device).isdigit():
        raise ValueError("Usa CPU o una sola GPU configurada en el servidor.")
    if architecture not in ALLOWED_BASES:
        raise ValueError("Solo se admiten pesos base YOLOv8n/YOLOv8s preentrenados.")
    if set(parameters) - PARAMETERS:
        raise ValueError("Configuración de entrenamiento no permitida.")
    if model_factory is None:
        from ultralytics import YOLO

        model_factory = YOLO
    weights_dir = Path(weights_dir)
    weights_dir.mkdir(parents=True, exist_ok=True)
    base = weights_dir / architecture
    # Passing an explicit trusted basename lets Ultralytics download its official pretrained release.
    model = model_factory(str(base))
    if not base.is_file():
        raise ValueError(
            "No se encontraron los pesos preentrenados. Prepara AI_BASE_WEIGHTS_DIR antes de reintentar."
        )
    base_hash = file_sha256(base)
    on_start({"base_weights_sha256": base_hash, "pretrained": True})

    active_epoch = None

    def epoch_start(trainer):
        nonlocal active_epoch
        active_epoch = int(trainer.epoch) + 1

    def epoch_callback(trainer):
        nonlocal active_epoch
        # Newer Ultralytics runs on_fit_epoch_end once more during best-weight
        # evaluation, without a new training epoch. Never invent epoch N+1.
        if active_epoch is None:
            return
        number, active_epoch = active_epoch, None
        on_epoch(number, finite_metrics(trainer.metrics))

    model.add_callback("on_train_epoch_start", epoch_start)
    model.add_callback("on_fit_epoch_end", epoch_callback)
    start = perf_counter()
    log_handler = None
    try:
        from ultralytics.utils import LOGGER

        fit = Path(output_dir) / "fit"
        fit.mkdir(parents=True, exist_ok=True)
        log_handler = logging.FileHandler(fit / "console.log", encoding="utf-8")
        LOGGER.addHandler(log_handler)
    except ImportError:
        LOGGER = None
    try:
        results = model.train(
            data=str(data_yaml),
            project=str(output_dir),
            name="fit",
            exist_ok=True,
            device=device,
            workers=0,
            plots=True,
            save=True,
            val=True,
            pretrained=True,
            amp=False,
            **parameters,
        )
    finally:
        if log_handler is not None:
            LOGGER.removeHandler(log_handler)
            log_handler.close()
    total_seconds = perf_counter() - start
    best = Path(model.trainer.best)
    if not best.is_file():
        raise ValueError(
            "El entrenamiento terminó sin best.pt; no se registrará un modelo incompleto."
        )
    names = model.names
    if len(names) != 1 or str(names[0]).lower() != "rona":
        raise ValueError("El modelo entrenado no coincide con la clase única 0: rona.")
    return {
        "best": best,
        "last": Path(model.trainer.last),
        "save_dir": Path(model.trainer.save_dir),
        "metrics": finite_metrics(results.results_dict),
        "duration_seconds": total_seconds,
        "effective_parameters": {
            key: getattr(model.trainer.args, key, None) for key in PARAMETERS
        },
        "base_weights_sha256": base_hash,
        "weights_sha256": file_sha256(best),
    }
