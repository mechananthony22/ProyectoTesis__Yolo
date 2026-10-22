import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from django.conf import settings
from apps.research import tasks
from apps.research.models import Job, TrainingRun, AIModel
from ai.training import finite_metrics, train_model, file_sha256
from .helpers import dataset_version

pytestmark = pytest.mark.django_db


def run_fixture(user):
    ds, version = dataset_version(user)
    job = Job.objects.create(
        owner=user,
        kind="training",
        config={
            "version": str(version.pk),
            "architecture": "yolov8n.pt",
            "epochs": 2,
            "batch": 2,
            "imgsz": 640,
            "device": "cpu",
        },
    )
    return TrainingRun.objects.create(version=version, job=job), job


def fake_training(**kwargs):
    folder = Path(kwargs["output_dir"]) / "fit"
    folder.mkdir(parents=True, exist_ok=True)
    best = folder / "weights/best.pt"
    best.parent.mkdir()
    best.write_bytes(b"trusted-test-weights")
    last = best.with_name("last.pt")
    last.write_bytes(b"last-test-weights")
    (folder / "results.csv").write_text("epoch,metric\n1,0.1\n2,0.2\n")
    kwargs["on_start"]({"base_weights_sha256": "test-hash", "pretrained": True})
    kwargs["on_epoch"](1, {"metrics/mAP50(B)": 0.1})
    kwargs["on_epoch"](2, {"metrics/mAP50(B)": 0.2})
    kwargs["on_epoch"](2, {"metrics/mAP50(B)": 0.21})
    return {
        "best": best,
        "last": last,
        "save_dir": folder,
        "metrics": {"metrics/mAP50(B)": 0.21, "missing": None},
        "duration_seconds": 1.25,
        "weights_sha256": file_sha256(best),
    }


def test_metrics_are_json_safe_and_undefined_not_zero():
    result = finite_metrics(
        {"valid": 0.8, "nan": float("nan"), "infinite": float("inf"), "none": None}
    )
    assert result == {"valid": 0.8, "nan": None, "infinite": None, "none": None}
    json.dumps(result, allow_nan=False)


def test_training_saves_progress_weights_artifacts_and_is_idempotent(user):
    run, job = run_fixture(user)
    with (
        patch("ai.training.environment", return_value={"device": "cpu"}),
        patch("ai.training.train_model", side_effect=fake_training),
    ):
        tasks.train(str(job.pk))
        tasks.train(str(job.pk))
    run.refresh_from_db()
    job.refresh_from_db()
    assert job.state == "succeeded" and job.progress == 100
    assert run.attempt == 1 and run.duration_seconds == 1.25
    assert [e["epoch"] for e in run.epochs_log] == [1, 2]
    assert run.epochs_log[-1]["metrics"]["metrics/mAP50(B)"] == 0.21
    assert run.environment["pretrained"] is True
    model = AIModel.objects.get(run=run)
    assert not model.active and model.sha256 == file_sha256(model.weights.path)
    artifacts = (
        Path(settings.MEDIA_ROOT) / "training-artifacts" / str(run.pk) / "attempt-1/fit"
    )
    assert (artifacts / "best.pt").is_file() and (artifacts / "last.pt").is_file()
    assert (
        json.loads((artifacts / "experiment.json").read_text())["weights_sha256"]
        == model.sha256
    )
    assert AIModel.objects.filter(run=run).count() == 1


def test_training_failure_keeps_progress_and_does_not_publish_model(user):
    run, job = run_fixture(user)

    def fail(**kwargs):
        kwargs["on_epoch"](1, {"metrics/mAP50(B)": float("nan")})
        raise RuntimeError("GPU memory exhausted")

    with (
        patch("ai.training.environment", return_value={"device": "cpu"}),
        patch("ai.training.train_model", side_effect=fail),
    ):
        tasks.train(str(job.pk))
    run.refresh_from_db()
    job.refresh_from_db()
    assert job.state == "failed" and "GPU memory" in job.error
    assert run.epochs_log[0]["metrics"]["metrics/mAP50(B)"] is None
    assert not AIModel.objects.filter(run=run).exists()
    assert (
        Path(settings.MEDIA_ROOT)
        / "training-artifacts"
        / str(run.pk)
        / "attempt-1/fit/failure.json"
    ).exists()


def test_retry_uses_new_attempt_without_overwriting_previous_artifacts(user):
    run, job = run_fixture(user)
    with (
        patch("ai.training.environment", return_value={"device": "cpu"}),
        patch("ai.training.train_model", side_effect=RuntimeError("interrupted")),
    ):
        tasks.train(str(job.pk))
    job.refresh_from_db()
    job.state = "queued"
    job.save()
    with (
        patch("ai.training.environment", return_value={"device": "cpu"}),
        patch("ai.training.train_model", side_effect=fake_training),
    ):
        tasks.train(str(job.pk))
    run.refresh_from_db()
    assert run.attempt == 2
    root = Path(settings.MEDIA_ROOT) / "training-artifacts" / str(run.pk)
    assert (root / "attempt-1/fit/failure.json").exists()
    assert (root / "attempt-2/fit/best.pt").exists()


def test_artifacts_are_owner_protected(client, user, other):
    run, job = run_fixture(other)
    assert client.get(f"/api/v1/training-runs/{run.pk}/artifacts/").status_code == 404
    run, job = run_fixture(user)
    with (
        patch("ai.training.environment", return_value={"device": "cpu"}),
        patch("ai.training.train_model", side_effect=fake_training),
    ):
        tasks.train(str(job.pk))
    result = client.get(f"/api/v1/training-runs/{run.pk}/artifacts/")
    assert result.status_code == 200 and "experiment.json" in result.data
    assert (
        client.get(
            f"/api/v1/training-runs/{run.pk}/artifacts/?name=../best.pt"
        ).status_code
        == 400
    )
    response = client.get(f"/api/v1/training-runs/{run.pk}/artifacts/?name=best.pt")
    assert b"".join(response.streaming_content) == b"trusted-test-weights"


def test_ai_resource_exclusion_keeps_second_job_from_running(user):
    from filelock import FileLock
    import threading

    run, job = run_fixture(user)
    ready = threading.Event()
    release = threading.Event()

    def hold():
        with FileLock(settings.AI_RESOURCE_LOCK):
            ready.set()
            release.wait(5)

    worker = threading.Thread(target=hold)
    worker.start()
    assert ready.wait(2)
    try:
        with patch("ai.training.train_model") as train:
            tasks.train(str(job.pk))
            assert not train.called
        job.refresh_from_db()
        assert job.state == "failed" and "ocupado" in job.error
    finally:
        release.set()
        worker.join()


def test_researcher_cannot_train_other_users_version(client, other):
    ds, version = dataset_version(other)
    response = client.post(
        "/api/v1/training-runs/",
        {"version": str(version.pk), "architecture": "yolov8n.pt"},
        format="json",
    )
    assert response.status_code == 404


def test_device_is_server_controlled_and_not_an_arbitrary_command(client, user):
    ds, version = dataset_version(user)
    response = client.post(
        "/api/v1/training-runs/",
        {"version": str(version.pk), "architecture": "yolov8n.pt", "device": "0,1,2"},
        format="json",
    )
    assert response.status_code == 400


def test_adapter_does_not_count_best_weight_evaluation_as_extra_epoch(tmp_path):
    events = []

    class FakeModel:
        names = {0: "rona"}

        def __init__(self, path):
            Path(path).write_bytes(b"fixture-pretrained")
            self.callbacks = {}

        def add_callback(self, name, callback):
            self.callbacks[name] = callback

        def train(self, **kwargs):
            folder = Path(kwargs["project"]) / "fit"
            folder.mkdir(parents=True, exist_ok=True)
            best = folder / "best.pt"
            best.write_bytes(b"fixture-trained")
            self.trainer = SimpleNamespace(
                epoch=0,
                metrics={"metric": 0.1},
                best=best,
                last=best,
                save_dir=folder,
                args=SimpleNamespace(epochs=2),
            )
            for index in [0, 1]:
                self.trainer.epoch = index
                self.callbacks["on_train_epoch_start"](self.trainer)
                self.callbacks["on_fit_epoch_end"](self.trainer)
            self.trainer.epoch = 2
            self.callbacks["on_fit_epoch_end"](self.trainer)
            return SimpleNamespace(results_dict={"metric": 0.2})

    result = train_model(
        data_yaml=tmp_path / "data.yaml",
        architecture="yolov8n.pt",
        weights_dir=tmp_path / "base",
        output_dir=tmp_path / "out",
        parameters={"epochs": 2},
        device="cpu",
        on_start=lambda x: None,
        on_epoch=lambda number, metrics: events.append(number),
        model_factory=FakeModel,
    )
    assert events == [1, 2] and result["metrics"] == {"metric": 0.2}
