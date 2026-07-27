import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def auth_client(db):
    User.objects.create_user(
        email="me@example.com", full_name="Me", password="s3cret-pass-123"
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": "me@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    return client


@pytest.mark.django_db
def test_detail_returns_card(auth_client):
    other = User.objects.create_user(
        email="other@example.com", full_name="Other Person",
        password="s3cret-pass-123", default_avatar="bob",
    )
    response = auth_client.get(f"/api/users/{other.id}/")
    assert response.status_code == 200
    assert response.data["email"] == "other@example.com"
    assert response.data["full_name"] == "Other Person"
    assert response.data["default_avatar"] == "bob"


@pytest.mark.django_db
def test_detail_404_for_missing_user(auth_client):
    response = auth_client.get("/api/users/999999/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_requires_authentication():
    other = User.objects.create_user(
        email="other@example.com", full_name="Other", password="s3cret-pass-123"
    )
    client = APIClient()
    response = client.get(f"/api/users/{other.id}/")
    assert response.status_code == 401
