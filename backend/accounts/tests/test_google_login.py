from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

CLAIMS = {
    "sub": "google-sub-123",
    "email": "gina@example.com",
    "email_verified": True,
    "name": "Gina Google",
    "picture": "https://lh3.googleusercontent.com/pic.jpg",
}


def _post(client, token="tok"):
    return client.post("/api/auth/google/", {"id_token": token}, format="json")


@patch("accounts.api.views.verify_google_id_token")
@pytest.mark.django_db
def test_new_google_user_is_created_and_logged_in(mock_verify):
    mock_verify.return_value = dict(CLAIMS)
    response = _post(APIClient())
    assert response.status_code == 200
    assert response.data["user"]["email"] == "gina@example.com"
    assert response.data["user"]["full_name"] == "Gina Google"
    assert response.data["user"]["avatar_url"] == CLAIMS["picture"]
    assert settings.AUTH_COOKIE_ACCESS in response.cookies
    assert "csrftoken" in response.cookies

    user = User.objects.get(email="gina@example.com")
    assert user.google_sub == "google-sub-123"
    assert user.privacy_accepted_at is not None
    assert not user.has_usable_password()


@patch("accounts.api.views.verify_google_id_token")
@pytest.mark.django_db
def test_returning_google_user_matches_by_sub_no_duplicate(mock_verify):
    mock_verify.return_value = dict(CLAIMS)
    _post(APIClient())
    _post(APIClient())
    assert User.objects.filter(google_sub="google-sub-123").count() == 1


@patch("accounts.api.views.verify_google_id_token")
@pytest.mark.django_db
def test_existing_email_account_is_linked(mock_verify):
    existing = User.objects.create_user(
        email="gina@example.com", full_name="Gina Password", password="s3cret-pass-123"
    )
    mock_verify.return_value = dict(CLAIMS)
    response = _post(APIClient())
    assert response.status_code == 200
    existing.refresh_from_db()
    assert existing.google_sub == "google-sub-123"
    assert User.objects.filter(email__iexact="gina@example.com").count() == 1


@patch("accounts.api.views.verify_google_id_token")
@pytest.mark.django_db
def test_unverified_email_is_rejected(mock_verify):
    mock_verify.return_value = {**CLAIMS, "email_verified": False}
    response = _post(APIClient())
    assert response.status_code == 401
    assert not User.objects.filter(email="gina@example.com").exists()


@patch("accounts.api.views.verify_google_id_token")
@pytest.mark.django_db
def test_invalid_token_is_rejected(mock_verify):
    from accounts.google import GoogleTokenError

    mock_verify.side_effect = GoogleTokenError("bad")
    response = _post(APIClient())
    assert response.status_code == 401


@pytest.mark.django_db
def test_missing_token_is_400():
    response = APIClient().post("/api/auth/google/", {}, format="json")
    assert response.status_code == 400
