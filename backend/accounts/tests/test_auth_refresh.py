import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def logged_in_client(db):
    User.objects.create_user(
        email="alice@example.com", full_name="Alice", password="s3cret-pass"
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": "alice@example.com", "password": "s3cret-pass"},
        format="json",
    )
    return client


@pytest.mark.django_db
def test_refresh_issues_new_access_cookie(logged_in_client):
    response = logged_in_client.post("/api/auth/refresh/", format="json")
    assert response.status_code == 200
    assert settings.AUTH_COOKIE_ACCESS in response.cookies
    assert response.cookies[settings.AUTH_COOKIE_ACCESS].value != ""


@pytest.mark.django_db
def test_refresh_without_cookie_is_rejected():
    client = APIClient()
    response = client.post("/api/auth/refresh/", format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_rotated_refresh_token_is_recorded_as_outstanding():
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

    user = User.objects.create_user(
        email="rotate@example.com", full_name="Rotate", password="s3cret-pass-123"
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": user.email, "password": "s3cret-pass-123"},
        format="json",
    )
    assert client.post("/api/auth/refresh/").status_code == 200

    rotated = client.cookies[settings.AUTH_COOKIE_REFRESH].value
    assert OutstandingToken.objects.filter(user=user, token=rotated).exists()
