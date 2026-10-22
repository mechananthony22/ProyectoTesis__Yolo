"""Real pretrained YOLOv8 training on geometric fixtures, never thesis evidence."""

import os
import io
import json
from pathlib import Path
import pytest
from PIL import Image, ImageDraw
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from apps.research.models import Dataset, Job, TrainingRun, AIModel
from apps.research.services import import_images, annotate, freeze
from apps.research.tasks import train

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        os.getenv("AI_SMOKE") != "1",
        reason="Requires locked AI worker environment and pretrained YOLOv8 weights",
    ),
]


def test_real_pretrained_yolov8_training_persists_model_and_artifacts(user, tmp_path):
    import torch

    torch.set_num_threads(2)
    settings.AI_DEVICE = "cpu"
    settings.AI_BASE_WEIGHTS_DIR = Path(
        os.getenv("AI_BASE_WEIGHTS_DIR", str(tmp_path / "base-weights"))
    )
    dataset = Dataset.objects.create(
        owner=user, name="TECHNICAL FIXTURE ONLY · geometric squares"
    )
    for split, n in [("train", 4), ("val", 2), ("test", 2)]:
        for index in range(n):
            image = Image.new(
                "RGB",
                (128, 128),
                (240, 235 - index - {"train": 0, "val": 40, "test": 80}[split], 220),
            )
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                (32 + index, 32, 96 + index, 96), fill=(50 + index * 10, 100, 50)
            )
            output = io.BytesIO()
            image.save(output, format="PNG")
            name = f"{split}-{index}.png"
            import_images(
                dataset,
                [SimpleUploadedFile(name, output.getvalue())],
                user,
                fruit_code=f"{split}-group-{index}",
            )
            asset = dataset.images.get(name=name)
            asset.split = split
            asset.save()
            annotate(
                asset,
                user,
                [
                    {
                        "class_id": 0,
                        "x": (64 + index) / 128,
                        "y": 0.5,
                        "w": 0.5,
                        "h": 0.5,
                    }
                ],
                "lesion",
                0,
                note="SYNTHETIC TECHNICAL FIXTURE, not avocado/scab data",
            )
    version = freeze(dataset, user, 42, {})
    config = {
        "version": str(version.pk),
        "architecture": "yolov8n.pt",
        "epochs": 2,
        "batch": 2,
        "imgsz": 640,
        "optimizer": "SGD",
        "lr0": 0.001,
        "weight_decay": 0.0005,
        "patience": 0,
        "seed": 42,
        "fliplr": 0.0,
        "degrees": 0.0,
        "hsv_v": 0.0,
        "device": "cpu",
    }
    job = Job.objects.create(owner=user, kind="training", config=config)
    run = TrainingRun.objects.create(
        job=job, version=version, architecture="yolov8n.pt"
    )
    if os.getenv("REDIS_INTEGRATION") == "1":
        import subprocess, sys, time, uuid
        from django.db import connection
        from config.celery import app

        assert connection.vendor == "postgresql"
        queue = "ai-smoke-" + uuid.uuid4().hex
        env = {
            **os.environ,
            "DJANGO_SETTINGS_MODULE": "config.ci_settings",
            "POSTGRES_DB": connection.settings_dict["NAME"],
            "MEDIA_ROOT": str(settings.MEDIA_ROOT),
            "AI_BASE_WEIGHTS_DIR": str(settings.AI_BASE_WEIGHTS_DIR),
            "AI_RESOURCE_LOCK": settings.AI_RESOURCE_LOCK,
            "OMP_NUM_THREADS": "2",
            "MKL_NUM_THREADS": "2",
        }
        with (tmp_path / "ai-worker.log").open("w+") as log:
            worker = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "celery",
                    "-A",
                    "config",
                    "worker",
                    "-P",
                    "solo",
                    "--concurrency=1",
                    "--without-gossip",
                    "--without-mingle",
                    "--without-heartbeat",
                    "-Q",
                    queue,
                    "--loglevel=warning",
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                app.send_task(
                    "apps.research.tasks.train", args=[str(job.pk)], queue=queue
                )
                deadline = time.monotonic() + 180
                while time.monotonic() < deadline:
                    job.refresh_from_db()
                    if (
                        job.state in ["succeeded", "failed"]
                        or worker.poll() is not None
                    ):
                        break
                    time.sleep(0.25)
                if job.state != "succeeded":
                    log.seek(0)
                    pytest.fail(
                        f"AI worker failed: {job.state}: {job.error}. {log.read()[-4000:]}"
                    )
            finally:
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=5)
    else:
        train(str(job.pk))
    job.refresh_from_db()
    run.refresh_from_db()
    assert job.state == "succeeded", job.error
    assert job.progress == 100 and run.attempt == 1
    assert [row["epoch"] for row in run.epochs_log] == [1, 2]
    assert run.environment["pretrained"] is True
    assert len(run.environment["base_weights_sha256"]) == 64
    assert run.duration_seconds is not None and run.duration_seconds > 0
    model = AIModel.objects.get(run=run)
    assert not model.active and Path(model.weights.path).stat().st_size > 1000
    directory = (
        Path(settings.MEDIA_ROOT) / "training-artifacts" / str(run.pk) / "attempt-1/fit"
    )
    for filename in [
        "best.pt",
        "last.pt",
        "results.csv",
        "results.png",
        "experiment.json",
        "metrics.json",
        "training.jsonl",
        "console.log",
    ]:
        assert (directory / filename).is_file(), filename
    json.dumps(run.metrics, allow_nan=False)
    # Confirm saved weights can be loaded, not accuracy: this is a technical smoke only.
    from ultralytics import YOLO

    loaded = YOLO(model.weights.path)
    assert loaded.names == {0: "rona"}

    if os.getenv("AI_SMOKE_REPORT"):
        report = Path(os.environ["AI_SMOKE_REPORT"])
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "status": "passed",
                    "purpose": "TECHNICAL FIXTURE ONLY; not thesis evidence",
                    "epochs_recorded": len(run.epochs_log),
                    "pretrained": run.environment["pretrained"],
                    "weights_sha256": model.sha256,
                    "environment": run.environment,
                    "artifacts_verified": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
