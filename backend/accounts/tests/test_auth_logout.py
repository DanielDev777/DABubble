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
def test_logout_clears_cookies(logged_in_client):
    response = logged_in_client.post("/api/auth/logout/", format="json")
    assert response.status_code == 200
    # delete_cookie sets the cookie to an empty value with a past expiry
    assert response.cookies[settings.AUTH_COOKIE_ACCESS].value == ""
    assert response.cookies[settings.AUTH_COOKIE_REFRESH].value == ""


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(logged_in_client):
    # Capture the refresh token issued at login before logout clears the jar.
    refresh_value = logged_in_client.cookies[settings.AUTH_COOKIE_REFRESH].value

    logged_in_client.post("/api/auth/logout/", format="json")

    # Present the captured (now blacklisted) refresh token explicitly. It is a
    # valid, unexpired token, so a 401 here proves the blacklist rejected it.
    replay = APIClient()
    replay.cookies[settings.AUTH_COOKIE_REFRESH] = refresh_value
    response = replay.post("/api/auth/refresh/", format="json")
    assert response.status_code == 401
