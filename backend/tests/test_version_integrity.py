import io
import zipfile
from pathlib import Path
import pytest
from django.core.files.base import ContentFile
from rest_framework.exceptions import ValidationError
from apps.research.services import verify_version_archive
from apps.research.tasks import unpack
from .helpers import dataset_version

pytestmark = pytest.mark.django_db

def test_verified_snapshot_can_be_exported_and_unpacked(client, user, tmp_path):
    ds, version = dataset_version(user)
    verify_version_archive(version)
    response = client.get(f'/api/v1/versions/{version.pk}/download/')
    assert response.status_code == 200
    payload = b''.join(response.streaming_content)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert len([n for n in archive.namelist() if n.startswith('labels/')]) == 3
    config = unpack(version, tmp_path / 'snapshot')
    assert Path(config).is_file()
    assert all((tmp_path/'snapshot'/'images'/item['split']/item['file']).is_file() for item in version.manifest)

def test_corrupt_archive_is_not_downloaded_or_used(client, user):
    ds, version = dataset_version(user)
    version.archive.save('corrupt.zip', ContentFile(b'corrupt'))
    response = client.get(f'/api/v1/versions/{version.pk}/download/')
    assert response.status_code == 400
    with pytest.raises(ValidationError, match='modificado'):
        verify_version_archive(version)

def test_changed_label_file_breaks_snapshot_integrity(user):
    ds, version = dataset_version(user)
    output = io.BytesIO()
    with zipfile.ZipFile(version.archive.path) as source, zipfile.ZipFile(output, 'w') as target:
        for name in source.namelist():
            content = b'0 .1 .1 .1 .1' if name.startswith('labels/train') else source.read(name)
            target.writestr(name, content)
    version.archive.save('modified-labels.zip', ContentFile(output.getvalue()))
    with pytest.raises(ValidationError):
        verify_version_archive(version)

def test_changed_database_manifest_is_detected(user):
    ds, version = dataset_version(user)
    version.manifest[0]['annotations'] = []
    version.save(update_fields=['manifest'])
    with pytest.raises(ValidationError, match='manifiesto'):
        verify_version_archive(version)

def test_snapshot_from_other_owner_is_private(client, other):
    ds, version = dataset_version(other)
    assert client.get(f'/api/v1/versions/{version.pk}/download/').status_code == 404

def test_legacy_snapshot_requires_regeneration(user):
    ds, version = dataset_version(user)
    version.archive_sha256 = ''
    with pytest.raises(ValidationError, match='antigua'):
        verify_version_archive(version)
