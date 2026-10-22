import hashlib
import io
import json
import random
import zipfile
from pathlib import Path, PurePosixPath
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import (
    Dataset,
    ImageAsset,
    AnnotationHistory,
    DatasetVersion,
    AuditEvent,
    Job,
)
from .validation import inspect_image, parse_yolo, safe_zip_entries, ALLOWED_EXTENSIONS


def audit(user, action, obj, detail=None):
    AuditEvent.objects.create(
        actor=user, action=action, object_id=str(obj.pk), detail=detail or {}
    )


def import_images(dataset, uploads, user, source="", fruit_code=""):
    prepared = []
    for upload in uploads:
        if upload.size > 100 * 1024 * 1024:
            raise ValidationError("Cada carga está limitada a 100 MB.")
        if Path(upload.name).suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(upload) as archive:
                    entries = safe_zip_entries(archive)
                    names = {i.filename for i in entries if not i.is_dir()}
                    for info in entries:
                        if (
                            info.is_dir()
                            or Path(info.filename).suffix.lower()
                            not in ALLOWED_EXTENSIONS
                        ):
                            continue
                        path = PurePosixPath(info.filename)
                        label_parts = list(path.with_suffix(".txt").parts)
                        if "images" in label_parts:
                            label_parts[label_parts.index("images")] = "labels"
                        label = "/".join(label_parts)
                        # Also accepts train/images/a.jpg + train/labels/a.txt.
                        boxes = (
                            parse_yolo(archive.read(label).decode("utf-8-sig"))
                            if label in names
                            else []
                        )
                        split = next(
                            (
                                p
                                for p in path.parts
                                if p in ["train", "val", "valid", "test"]
                            ),
                            "",
                        )
                        if split == "valid":
                            split = "val"
                        data = archive.read(info)
                        prepared.append(
                            (
                                path.name,
                                data,
                                inspect_image(data, path.name),
                                boxes,
                                split,
                            )
                        )
            except (zipfile.BadZipFile, UnicodeDecodeError, RuntimeError):
                raise ValidationError(
                    "ZIP ilegible o etiquetas con codificación inválida."
                )
        else:
            data = upload.read()
            prepared.append(
                (Path(upload.name).name, data, inspect_image(data, upload.name), [], "")
            )
    if sum(item[2]["size"] for item in prepared) > 250 * 1024 * 1024:
        raise ValidationError("El total descomprimido excede 250 MB; divide la carga.")
    if not prepared:
        raise ValidationError("No se encontraron imágenes compatibles.")
    if len(prepared) > 2000:
        raise ValidationError("Carga limitada a 2000 imágenes.")
    created = []
    duplicates = []
    stored = []
    try:
        with transaction.atomic():
            Dataset.objects.select_for_update().get(pk=dataset.pk)
            for name, data, meta, boxes, split in prepared:
                if ImageAsset.objects.filter(
                    dataset=dataset, sha256=meta["sha256"]
                ).exists():
                    duplicates.append(name)
                    continue
                obj = ImageAsset(
                    dataset=dataset,
                    name=name,
                    source=source or dataset.source,
                    fruit_code=fruit_code,
                    annotations=boxes,
                    split=split,
                    **meta,
                )
                obj.file.save(
                    f"{obj.id}{Path(name).suffix.lower()}",
                    ContentFile(data),
                    save=False,
                )
                stored.append(obj.file.name)
                obj.save()
                created.append(str(obj.pk))
            audit(
                user,
                "dataset.import",
                dataset,
                {"created": len(created), "duplicates": len(duplicates)},
            )
    except Exception:
        from django.core.files.storage import default_storage

        for name in stored:
            default_storage.delete(name)
        raise
    return {
        "created": created,
        "duplicates": duplicates,
        "detail": "Etiquetas importadas pendientes de revisión humana. Asigna código de fruto/grupo antes de congelar.",
    }


@transaction.atomic
def annotate(image, user, boxes, state, revision, note=""):
    image = ImageAsset.objects.select_for_update().get(pk=image.pk)
    if image.revision != revision:
        raise ValidationError(
            "La imagen cambió. Recarga antes de guardar para no sobrescribir otra revisión."
        )
    if state == "healthy" and boxes:
        raise ValidationError("Una imagen sin lesiones revisadas no debe tener cajas.")
    if state == "lesion" and not boxes:
        raise ValidationError(
            "Marca al menos una lesión o usa el estado pendiente/sin lesiones."
        )
    image.annotations = boxes
    image.state = state
    image.revision += 1
    image.reviewed_by = user if state in ["healthy", "lesion"] else None
    image.reviewed_at = timezone.now() if image.reviewed_by else None
    image.save()
    AnnotationHistory.objects.create(
        image=image,
        author=user,
        revision=image.revision,
        annotations=boxes,
        state=state,
        note=note,
    )
    audit(user, "image.annotate", image, {"revision": image.revision})
    return image


@transaction.atomic
def split_dataset(dataset, ratios, seed, user):
    Dataset.objects.select_for_update().get(pk=dataset.pk)
    images = list(dataset.images.exclude(state="discarded").order_by("id"))
    if not images or any(not x.fruit_code.strip() for x in images):
        raise ValidationError(
            "Asigna un código de fruto/grupo a todas las imágenes antes de particionar."
        )
    groups = sorted(set(x.fruit_code for x in images))
    random.Random(seed).shuffle(groups)
    if len(groups) < 3:
        raise ValidationError("Se requieren al menos tres grupos independientes.")
    n = len(groups)
    nt = max(1, min(n - 2, round(n * ratios[0])))
    nv = max(1, min(n - nt - 1, round(n * ratios[1])))
    mapping = {
        g: ("train" if i < nt else "val" if i < nt + nv else "test")
        for i, g in enumerate(groups)
    }
    for x in images:
        x.split = mapping[x.fruit_code]
    ImageAsset.objects.bulk_update(images, ["split"])
    audit(user, "dataset.split", dataset, {"ratios": ratios, "seed": seed})
    return {s: sum(x.split == s for x in images) for s in ["train", "val", "test"]}


@transaction.atomic
def freeze(dataset, user, seed, variant_ids):
    Dataset.objects.select_for_update().get(pk=dataset.pk)
    images = list(dataset.images.exclude(state="discarded").order_by("id"))
    if not images or any(
        x.state == "pending"
        or not x.reviewed_by_id
        or not x.fruit_code.strip()
        or not x.split
        for x in images
    ):
        raise ValidationError(
            "Todas las imágenes incluidas deben estar revisadas, tener fruto/grupo y partición."
        )
    groups = {}
    hashes = {}
    for x in images:
        for mapping, key in [(groups, x.fruit_code), (hashes, x.sha256)]:
            if key in mapping and mapping[key] != x.split:
                raise ValidationError(
                    "Fuga de datos: un fruto o duplicado aparece en más de una partición."
                )
            mapping[key] = x.split
    if set(x.split for x in images) != {"train", "val", "test"}:
        raise ValidationError("La versión necesita imágenes de train, val y test.")
    if not any(x.annotations and x.split == "train" for x in images):
        raise ValidationError("Train requiere al menos una imagen con roña anotada.")
    manifest = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for image in images:
            selected = image
            if str(image.pk) in variant_ids:
                selected = image.variants.get(pk=variant_ids[str(image.pk)])
                if selected.source_revision is None or selected.source_revision != image.revision:
                    raise ValidationError("Un derivado usa una revisión anterior de las etiquetas. Regénéralo y revísalo antes de congelar.")
            data = selected.file.read()
            selected.file.close()
            digest = hashlib.sha256(data).hexdigest()
            if digest != selected.sha256:
                raise ValidationError(
                    "Un archivo cambió respecto de su hash registrado."
                )
            boxes = selected.annotations
            filename = f"{image.pk}{Path(selected.file.name).suffix}"
            archive.writestr(f"images/{image.split}/{filename}", data)
            labels = "\n".join(
                f"0 {b['x']:.8f} {b['y']:.8f} {b['w']:.8f} {b['h']:.8f}" for b in boxes
            )
            archive.writestr(f"labels/{image.split}/{image.pk}.txt", labels)
            manifest.append(
                {
                    "image_id": str(image.pk),
                    "fruit_code": image.fruit_code,
                    "split": image.split,
                    "sha256": digest,
                    "original_sha256": image.sha256,
                    "file": filename,
                    "annotations": boxes,
                    "annotation_revision": image.revision,
                    "reviewer_id": image.reviewed_by_id,
                    "variant_id": str(selected.pk) if selected is not image else None,
                    "variant_accepted_by": user.pk if selected is not image else None,
                }
            )
        if not any(item["annotations"] for item in manifest if item["split"] == "train"):
            raise ValidationError("Los archivos seleccionados para train no contienen lesiones anotadas. Revisa los recortes.")
        raw = json.dumps(manifest, sort_keys=True).encode()
        archive.writestr("manifest.json", raw)
        archive.writestr(
            "data.yaml",
            "path: .\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: rona\n",
        )
    number = (dataset.versions.aggregate(n=Max("number"))["n"] or 0) + 1
    archive_contents = buffer.getvalue()
    version = DatasetVersion(
        dataset=dataset,
        number=number,
        seed=seed,
        manifest=manifest,
        manifest_hash=hashlib.sha256(raw).hexdigest(),
        archive_sha256=hashlib.sha256(archive_contents).hexdigest(),
        created_by=user,
    )
    version.archive.save(
        f"{version.pk}.zip", ContentFile(archive_contents), save=False
    )
    version.save()
    audit(user, "dataset.freeze", version, {"number": number})
    return version


def dispatch(job, task):
    # Persistent queued row is the outbox; failed publication remains retryable by owner.
    try:
        result = task.apply_async(args=[str(job.pk)], retry=False)
        Job.objects.filter(pk=job.pk).update(task_id=result.id)
    except Exception:
        Job.objects.filter(pk=job.pk).update(
            error="No se pudo contactar Redis. Inicia Redis y el worker y pulsa Reenviar."
        )
    job.refresh_from_db()
    return job


def verify_version_archive(version):
    """Verify a frozen snapshot before download or worker extraction."""
    if not version.archive_sha256:
        raise ValidationError("Esta versión antigua no tiene hash del ZIP. Congela una nueva versión antes de usarla.")
    digest = hashlib.sha256()
    with version.archive.open("rb") as archive_file:
        for block in archive_file.chunks():
            digest.update(block)
    if digest.hexdigest() != version.archive_sha256:
        raise ValidationError("El ZIP de esta versión fue modificado o está corrupto; no se utilizará.")
    expected = json.dumps(version.manifest, sort_keys=True).encode()
    if hashlib.sha256(expected).hexdigest() != version.manifest_hash:
        raise ValidationError("El manifiesto no coincide con su hash; no se utilizará la versión.")
    with zipfile.ZipFile(version.archive.path) as archive:
        if archive.read("manifest.json") != expected:
            raise ValidationError("El manifiesto del ZIP no coincide con la versión congelada.")
