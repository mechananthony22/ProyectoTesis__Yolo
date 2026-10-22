import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User


@pytest.mark.django_db
def test_jwt_login_refresh_logout(user):
    c = APIClient()
    assert c.get("/api/v1/datasets/").status_code == 401
    bad = c.post("/api/v1/auth/token/", {"username": "anthony", "password": "bad"})
    assert bad.status_code == 401
    r = c.post(
        "/api/v1/auth/token/",
        {"username": "anthony", "password": "CorrectPassword-2387"},
    )
    assert r.status_code == 200
    c.credentials(HTTP_AUTHORIZATION="Bearer " + r.data["access"])
    assert c.get("/api/v1/users/me/").data["username"] == "anthony"
    refreshed = c.post("/api/v1/auth/refresh/", {"refresh": r.data["refresh"]})
    assert refreshed.status_code == 200
    assert (
        c.post("/api/v1/auth/refresh/", {"refresh": r.data["refresh"]}).status_code
        == 401
    )
    assert (
        c.post(
            "/api/v1/auth/logout/", {"refresh": refreshed.data["refresh"]}
        ).status_code
        == 200
    )
    assert (
        c.post(
            "/api/v1/auth/refresh/", {"refresh": refreshed.data["refresh"]}
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_profile_cannot_escalate_role(client, user):
    r = client.patch(
        "/api/v1/users/me/",
        {"role": "admin", "is_superuser": True, "first_name": "Anthony"},
        format="json",
    )
    assert r.status_code == 200
    user.refresh_from_db()
    assert (
        user.role == "researcher"
        and not user.is_superuser
        and user.first_name == "Anthony"
    )
    assert client.get("/api/v1/users/").status_code == 403
    assert (
        client.post(
            "/api/v1/users/", {"username": "bad", "password": "password"}
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_admin_creates_user_and_password_validation(admin):
    c = APIClient()
    c.force_authenticate(admin)
    assert (
        c.post("/api/v1/users/", {"username": "new", "password": "123"}).status_code
        == 400
    )
    r = c.post(
        "/api/v1/users/",
        {
            "username": "new",
            "password": "Long-Unique-Password-892",
            "role": "researcher",
        },
    )
    assert r.status_code == 201 and "password" not in r.data
    assert User.objects.get(username="new").check_password("Long-Unique-Password-892")


@pytest.mark.django_db
def test_deactivated_user_login(user):
    user.is_active = False
    user.save()
    assert (
        APIClient()
        .post(
            "/api/v1/auth/token/",
            {"username": "anthony", "password": "CorrectPassword-2387"},
        )
        .status_code
        == 401
    )
