import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import DEFAULT_AVATAR_SLUGS

User = get_user_model()


def _payload(**overrides):
    data = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "password": "s3cret-pass-123",
        "consent": True,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_signup_creates_user_and_auto_logs_in():
    client = APIClient()
    response = client.post("/api/auth/signup/", _payload(), format="json")
    assert response.status_code == 201
    assert response.data["user"]["email"] == "ada@example.com"
    assert response.data["user"]["full_name"] == "Ada Lovelace"
    assert response.data["user"]["default_avatar"] in DEFAULT_AVATAR_SLUGS
    assert settings.AUTH_COOKIE_ACCESS in response.cookies
    assert settings.AUTH_COOKIE_REFRESH in response.cookies

    user = User.objects.get(email="ada@example.com")
    assert user.full_name == "Ada Lovelace"
    assert user.privacy_accepted_at is not None
    assert user.default_avatar in DEFAULT_AVATAR_SLUGS


@pytest.mark.django_db
def test_signup_sets_csrf_cookie():
    # Auto-login is followed by the avatar-selection PATCH, which needs CSRF.
    client = APIClient()
    response = client.post("/api/auth/signup/", _payload(), format="json")
    assert response.status_code == 201
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_signup_requires_consent():
    client = APIClient()
    response = client.post("/api/auth/signup/", _payload(consent=False), format="json")
    assert response.status_code == 400
    assert not User.objects.filter(email="ada@example.com").exists()


@pytest.mark.django_db
def test_signup_rejects_weak_password():
    client = APIClient()
    response = client.post("/api/auth/signup/", _payload(password="123"), format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_signup_rejects_duplicate_email():
    User.objects.create_user(
        email="ada@example.com", full_name="Existing", password="s3cret-pass-123"
    )
    client = APIClient()
    response = client.post("/api/auth/signup/", _payload(), format="json")
    assert response.status_code == 400
