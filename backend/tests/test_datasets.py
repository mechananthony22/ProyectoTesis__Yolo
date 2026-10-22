import io
import zipfile
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from apps.research.models import Dataset
from apps.research.services import import_images, annotate, freeze, split_dataset
from apps.research.validation import parse_yolo
from .helpers import upload, png, dataset_version

pytestmark = pytest.mark.django_db


def test_owner_isolation_and_private_file(client, user, other):
    ds = Dataset.objects.create(owner=other, name="Private")
    import_images(ds, [upload()], other)
    image = ds.images.first()
    assert client.get(f"/api/v1/datasets/{ds.pk}/").status_code == 404
    assert client.get(f"/api/v1/images/{image.pk}/file/").status_code == 404
    assert (
        client.patch(
            f"/api/v1/images/{image.pk}/", {"fruit_code": "hacked"}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/datasets/").data["count"] == 0


def test_import_labels_deduplicate_pending(client, user):
    ds = Dataset.objects.create(owner=user, name="Existing dataset")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("images/train/a.png", png())
        z.writestr("labels/train/a.txt", "0 .5 .5 .2 .3")
    f = SimpleUploadedFile("dataset.zip", buf.getvalue())
    r = client.post(
        f"/api/v1/datasets/{ds.pk}/import/", {"files": [f]}, format="multipart"
    )
    assert r.status_code == 201
    image = ds.images.get()
    assert (
        image.split == "train"
        and image.state == "pending"
        and len(image.annotations) == 1
    )
    r = client.post(
        f"/api/v1/datasets/{ds.pk}/import/", {"files": [upload()]}, format="multipart"
    )
    assert r.status_code == 201 and len(r.data["duplicates"]) == 1


def test_zip_path_traversal_rejected(user):
    ds = Dataset.objects.create(owner=user, name="Safe")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("../outside.png", png())
    with pytest.raises(ValidationError):
        import_images(ds, [SimpleUploadedFile("bad.zip", buf.getvalue())], user)
    assert not ds.images.exists()


@pytest.mark.parametrize(
    "line", ["1 .5 .5 .2 .2", "0 .5 .5 -1 .2", "0 nan .5 .2 .2", "0 .1 .1 .9 .9"]
)
def test_invalid_yolo(line):
    with pytest.raises(ValidationError):
        parse_yolo(line)


def test_annotation_revision_and_negative_rules(client, user):
    ds = Dataset.objects.create(owner=user, name="A")
    import_images(ds, [upload()], user)
    img = ds.images.get()
    box = {"class_id": 0, "x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2}
    endpoint = f"/api/v1/images/{img.pk}/annotate/"
    assert (
        client.post(
            endpoint,
            {"annotations": [box], "state": "healthy", "revision": 0},
            format="json",
        ).status_code
        == 400
    )
    assert (
        client.post(
            endpoint,
            {"annotations": [], "state": "healthy", "revision": 0},
            format="json",
        ).status_code
        == 200
    )
    assert (
        client.post(
            endpoint,
            {"annotations": [box], "state": "lesion", "revision": 0},
            format="json",
        ).status_code
        == 400
    )
    img.refresh_from_db()
    assert img.revision == 1 and img.history.count() == 1


def test_snapshot_immutable_and_export_labels(user):
    ds, version = dataset_version(user)
    original = version.manifest.copy()
    image = ds.images.filter(split="train").get()
    annotate(image, user, [], "healthy", image.revision)
    version.refresh_from_db()
    assert version.manifest == original and version.manifest[0]["annotations"]
    with zipfile.ZipFile(version.archive.path) as z:
        assert "data.yaml" in z.namelist()
        assert len([x for x in z.namelist() if x.endswith(".txt")]) == 3


def test_freeze_rejects_group_leakage(user):
    ds, version = dataset_version(user)
    ds.images.update(fruit_code="same-fruit")
    with pytest.raises(ValidationError):
        freeze(ds, user, 42, {})
    assert ds.versions.count() == 1


def test_split_requires_group_and_keeps_same_group(user):
    ds = Dataset.objects.create(owner=user, name="Groups")
    for i in range(6):
        import_images(ds, [upload(f"{i}.png", (i * 30, 0, 0))], user)
    with pytest.raises(ValidationError):
        split_dataset(ds, [0.7, 0.2, 0.1], 42, user)
    for i, image in enumerate(ds.images.order_by("name")):
        image.fruit_code = f"fruit-{i // 2}"
        image.save()
    split_dataset(ds, [0.7, 0.2, 0.1], 42, user)
    for fruit in ["fruit-0", "fruit-1", "fruit-2"]:
        assert (
            ds.images.filter(fruit_code=fruit).values("split").distinct().count() == 1
        )


def test_unreviewed_not_negative(user):
    ds = Dataset.objects.create(owner=user, name="Pending")
    import_images(ds, [upload()], user, fruit_code="F01")
    with pytest.raises(ValidationError):
        freeze(ds, user, 42, {})
