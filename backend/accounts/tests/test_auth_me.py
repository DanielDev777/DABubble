import pytest
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
def test_me_returns_current_user(logged_in_client):
    response = logged_in_client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["email"] == "alice@example.com"
    assert response.data["full_name"] == "Alice"


@pytest.mark.django_db
def test_me_requires_authentication():
    client = APIClient()
    response = client.get("/api/auth/me/")
    assert response.status_code == 401
