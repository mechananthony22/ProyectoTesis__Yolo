import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.research.models import Dataset
from apps.research.services import import_images, annotate, freeze


def png(color=(120, 160, 80), size=(100, 80)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format="PNG")
    return out.getvalue()


def upload(name="fruit.png", color=(120, 160, 80)):
    return SimpleUploadedFile(name, png(color), content_type="image/png")


def dataset_version(user):
    ds = Dataset.objects.create(owner=user, name="Test fixture")
    for index, split in enumerate(["train", "val", "test"]):
        import_images(
            ds,
            [upload(f"{index}.png", (100 + index * 20, 80, 40))],
            user,
            fruit_code=f"F{index}",
        )
        image = ds.images.get(name=f"{index}.png")
        image.split = split
        image.save()
        annotate(
            image,
            user,
            [{"class_id": 0, "x": 0.5, "y": 0.5, "w": 0.2, "h": 0.2}],
            "lesion",
            0,
        )
    return ds, freeze(ds, user, 42, {})
