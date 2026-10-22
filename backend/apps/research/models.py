import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator, MaxValueValidator


class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class Dataset(Record):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=500, blank=True)
    license = models.CharField(max_length=200, blank=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ImageAsset(Record):
    STATES = [
        ("pending", "Pendiente"),
        ("healthy", "Sin lesiones anotadas"),
        ("lesion", "Con roña"),
        ("discarded", "Descartada"),
    ]
    dataset = models.ForeignKey(
        Dataset, on_delete=models.PROTECT, related_name="images"
    )
    file = models.FileField(upload_to="originals/%Y/%m")
    name = models.CharField(max_length=240)
    sha256 = models.CharField(max_length=64, db_index=True)
    perceptual_hash = models.CharField(max_length=16)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    size = models.PositiveIntegerField()
    source = models.CharField(max_length=500, blank=True)
    fruit_code = models.CharField(
        max_length=120,
        blank=True,
        help_text="Mismo código para fotos del mismo fruto o grupo relacionado.",
    )
    split = models.CharField(
        max_length=10,
        choices=[
            ("", "Sin asignar"),
            ("train", "Train"),
            ("val", "Validación"),
            ("test", "Prueba"),
        ],
        blank=True,
    )
    state = models.CharField(max_length=12, choices=STATES, default="pending")
    annotations = models.JSONField(default=list)
    revision = models.PositiveIntegerField(default=0)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    quality = models.JSONField(default=dict)

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "sha256"], name="unique_image_in_dataset"
            )
        ]


class AnnotationHistory(Record):
    image = models.ForeignKey(
        ImageAsset, on_delete=models.PROTECT, related_name="history"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    annotations = models.JSONField(default=list)
    state = models.CharField(max_length=12)
    note = models.TextField(blank=True)

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["image", "revision"], name="unique_annotation_revision"
            )
        ]


class DatasetVersion(Record):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.PROTECT, related_name="versions"
    )
    number = models.PositiveIntegerField()
    seed = models.PositiveIntegerField(default=42)
    manifest = models.JSONField(default=list)
    manifest_hash = models.CharField(max_length=64)
    archive_sha256 = models.CharField(max_length=64, blank=True, default="")
    archive = models.FileField(upload_to="versions")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "number"], name="unique_dataset_version"
            )
        ]


class Job(Record):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=20)
    state = models.CharField(
        max_length=20,
        default="queued",
        choices=[
            ("queued", "En cola"),
            ("running", "En proceso"),
            ("succeeded", "Completado"),
            ("failed", "Fallido"),
        ],
    )
    progress = models.PositiveIntegerField(default=0)
    config = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    error = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    task_id = models.CharField(max_length=100, blank=True)

    class Meta(Record.Meta):
        indexes = [models.Index(fields=["owner", "state", "created_at"])]


class ImageVariant(Record):
    source_revision = models.PositiveIntegerField(
        null=True,
        help_text="Revisión de etiquetas usada al procesar; NULL en derivados anteriores sin trazabilidad.",
    )
    image = models.ForeignKey(
        ImageAsset, on_delete=models.PROTECT, related_name="variants"
    )
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    file = models.FileField(upload_to="variants")
    recipe = models.JSONField(default=dict)
    annotations = models.JSONField(default=list)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)


class TrainingRun(Record):
    attempt = models.PositiveIntegerField(default=0)
    duration_seconds = models.FloatField(null=True, validators=[MinValueValidator(0)])
    version = models.ForeignKey(
        DatasetVersion, on_delete=models.PROTECT, related_name="runs"
    )
    job = models.OneToOneField(Job, on_delete=models.PROTECT)
    architecture = models.CharField(max_length=30, default="yolov8n.pt")
    metrics = models.JSONField(default=dict)
    epochs_log = models.JSONField(default=list)
    environment = models.JSONField(default=dict)


class AIModel(Record):
    run = models.ForeignKey(
        TrainingRun, on_delete=models.PROTECT, related_name="models"
    )
    name = models.CharField(max_length=160)
    weights = models.FileField(upload_to="models")
    sha256 = models.CharField(max_length=64)
    active = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True
    )

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["active"], condition=Q(active=True), name="one_active_model"
            )
        ]


class Inspection(Record):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    model = models.ForeignKey(AIModel, on_delete=models.PROTECT)
    job = models.OneToOneField(Job, on_delete=models.PROTECT)
    original = models.FileField(upload_to="inspections")
    annotated = models.FileField(upload_to="results", blank=True)
    name = models.CharField(max_length=240)
    sha256 = models.CharField(max_length=64)
    detections = models.JSONField(default=list)
    inference_ms = models.FloatField(null=True, validators=[MinValueValidator(0)])
    total_ms = models.FloatField(null=True, validators=[MinValueValidator(0)])
    review = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pendiente"),
            ("confirmed", "Confirmada"),
            ("corrected", "Corregida"),
        ],
    )


class InspectionReview(Record):
    inspection = models.ForeignKey(
        Inspection, on_delete=models.PROTECT, related_name="reviews"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=20)
    note = models.TextField()
    annotations = models.JSONField(default=list)


class Evaluation(Record):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    protocol = models.TextField()
    version = models.ForeignKey(DatasetVersion, on_delete=models.PROTECT)
    model = models.ForeignKey(AIModel, on_delete=models.PROTECT)
    confidence = models.FloatField(
        default=0.25, validators=[MinValueValidator(0.01), MaxValueValidator(0.99)]
    )
    locked = models.BooleanField(default=False)
    metrics = models.JSONField(default=dict)
    job = models.ForeignKey(Job, on_delete=models.PROTECT, null=True)


class EvaluationSample(Record):
    evaluation = models.ForeignKey(
        Evaluation, on_delete=models.PROTECT, related_name="samples"
    )
    image_id_snapshot = models.CharField(max_length=36)
    fruit_code = models.CharField(max_length=120)
    truth = models.BooleanField()
    system_positive = models.BooleanField(null=True)
    system_ms = models.FloatField(null=True)

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["evaluation", "image_id_snapshot"],
                name="unique_evaluation_sample",
            )
        ]


class ManualObservation(Record):
    sample = models.ForeignKey(
        EvaluationSample, on_delete=models.PROTECT, related_name="observations"
    )
    observer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    participant = models.CharField(max_length=80)
    positive = models.BooleanField()
    elapsed_ms = models.FloatField(validators=[MinValueValidator(1)])

    class Meta(Record.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["sample", "participant"], name="one_manual_observation"
            )
        ]


class AuditEvent(Record):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    object_id = models.CharField(max_length=100)
    detail = models.JSONField(default=dict)
