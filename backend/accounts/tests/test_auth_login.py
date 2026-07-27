import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="alice@example.com", full_name="Alice", password="s3cret-pass"
    )


@pytest.mark.django_db
def test_login_sets_auth_cookies(user):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"email": "alice@example.com", "password": "s3cret-pass"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["user"]["email"] == "alice@example.com"
    assert settings.AUTH_COOKIE_ACCESS in response.cookies
    assert settings.AUTH_COOKIE_REFRESH in response.cookies
    assert response.cookies[settings.AUTH_COOKIE_ACCESS]["httponly"] is True


@pytest.mark.django_db
def test_login_rejects_bad_password(user):
    client = APIClient()
    response = client.post(
        "/api/auth/login/",
        {"email": "alice@example.com", "password": "wrong"},
        format="json",
    )
    assert response.status_code == 400
    assert settings.AUTH_COOKIE_ACCESS not in response.cookies
