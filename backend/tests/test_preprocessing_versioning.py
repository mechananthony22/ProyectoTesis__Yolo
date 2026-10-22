import hashlib
import io
import zipfile
import pytest
from PIL import Image
from django.core.files.base import ContentFile
from apps.research.models import Job, ImageVariant
from apps.research.services import annotate, freeze
from apps.research.tasks import preprocess
from ai.preprocessing import transform
from rest_framework.exceptions import ValidationError
from .helpers import dataset_version, png

pytestmark = pytest.mark.django_db

def derivative(user, image, crop=None):
    job = Job.objects.create(owner=user, kind='preprocessing', config={'images': [str(image.pk)], 'size': 800, 'crop': crop or [0, 0, 1, 1], 'brightness': 1, 'contrast': 1})
    preprocess(str(job.pk))
    job.refresh_from_db()
    assert job.state == 'succeeded'
    return ImageVariant.objects.get(job=job)

def test_derivative_remembers_source_and_preserves_original(user):
    ds, version = dataset_version(user)
    image = ds.images.filter(split='train').get()
    original = image.file.open('rb').read(); image.file.close()
    variant = derivative(user, image)
    assert variant.source_revision == image.revision
    assert hashlib.sha256(image.file.open('rb').read()).hexdigest() == hashlib.sha256(original).hexdigest()
    image.file.close()
    assert len(variant.annotations) == 1
    image_data = Image.open(variant.file.open('rb'))
    assert image_data.size == (800, 800)
    assert image_data.getpixel((1, 1)) == (255, 255, 255)
    image_data.close(); variant.file.close()

def test_derivative_with_old_labels_cannot_be_frozen(user):
    ds, version = dataset_version(user)
    image = ds.images.filter(split='train').get()
    variant = derivative(user, image)
    annotate(image, user, [{'class_id': 0, 'x': .5, 'y': .5, 'w': .3, 'h': .3}], 'lesion', image.revision)
    with pytest.raises(ValidationError, match='revisión anterior'):
        freeze(ds, user, 42, {str(image.pk): str(variant.pk)})
    assert ds.versions.count() == 1

def test_cropping_all_train_lesions_is_rejected(user):
    ds, version = dataset_version(user)
    image = ds.images.filter(split='train').get()
    variant = derivative(user, image, [0, 0, .2, 1])
    assert not variant.annotations
    with pytest.raises(ValidationError, match='no contienen lesiones'):
        freeze(ds, user, 42, {str(image.pk): str(variant.pk)})

def test_freeze_uses_transformed_annotations_and_matching_hash(user):
    ds, old_version = dataset_version(user)
    image = ds.images.filter(split='train').get()
    variant = derivative(user, image)
    version = freeze(ds, user, 42, {str(image.pk): str(variant.pk)})
    item = next(i for i in version.manifest if i['image_id'] == str(image.pk))
    assert item['variant_id'] == str(variant.pk)
    assert item['annotations'] == variant.annotations
    with zipfile.ZipFile(version.archive.path) as archive:
        assert hashlib.sha256(archive.read('images/train/' + item['file'])).hexdigest() == variant.sha256
        labels = archive.read(f'labels/train/{image.pk}.txt').decode()
        assert float(labels.split()[4]) == pytest.approx(variant.annotations[0]['h'], abs=1e-8)

@pytest.mark.parametrize('recipe', [
    {'size': 10},
    {'size': 800, 'crop': [.5, .5, .5, .7]},
    {'size': 640, 'crop': [0, 0, float('nan'), 1]},
    {'size': 800, 'brightness': float('inf')},
])
def test_invalid_processing_parameters_fail_before_derivative(recipe):
    with pytest.raises(ValueError):
        transform(png(), [], recipe)

def test_tiny_image_crop_reports_clear_error():
    with pytest.raises(ValueError, match='píxel'):
        transform(png(size=(1,1)), [], {'size':640, 'crop':[0,0,.1,.1]})

def test_broken_original_fails_job_without_derivative(user):
    ds, version = dataset_version(user)
    image = ds.images.filter(split='train').get()
    image.file.save('changed.png', ContentFile(png((1,2,3))))
    job = Job.objects.create(owner=user, kind='preprocessing', config={'images':[str(image.pk)], 'size':640})
    preprocess(str(job.pk)); job.refresh_from_db()
    assert job.state == 'failed' and not ImageVariant.objects.filter(job=job).exists()
    assert 'hash' in job.error
