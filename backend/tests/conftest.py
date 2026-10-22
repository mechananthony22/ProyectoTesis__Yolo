import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User


@pytest.fixture(autouse=True)
def isolated_storage(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_ROOT.mkdir()
    settings.AI_RESOURCE_LOCK = str(tmp_path / "ai.lock")


@pytest.fixture
def user(db):
    return User.objects.create_user(
        "anthony", password="CorrectPassword-2387", role="researcher"
    )


@pytest.fixture
def other(db):
    return User.objects.create_user("otro", password="OtherPassword-2387")


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        "admin", "admin@example.test", "AdminPassword-2387"
    )


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c
