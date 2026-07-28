import io
import os

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

User = get_user_model()


def _png_upload(name="a.png", size=(10, 10), content_type="image/png"):
    buffer = io.BytesIO()
    Image.new("RGB", size).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


def _gif_upload(name="a.gif"):
    # A real GIF (disallowed format) — DRF derives content_type from the bytes.
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buffer, format="GIF")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/gif")


def _big_png_over_2mb():
    # Random-noise PNG that does not compress, guaranteeing > 2 MB.
    buffer = io.BytesIO()
    Image.frombytes("RGB", (1200, 1200), os.urandom(1200 * 1200 * 3)).save(
        buffer, format="PNG"
    )
    buffer.seek(0)
    return SimpleUploadedFile("big.png", buffer.read(), content_type="image/png")


@pytest.fixture
def auth_client(db):
    User.objects.create_user(
        email="me@example.com", full_name="Me", password="s3cret-pass-123",
        default_avatar="bob",
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": "me@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    return client


@pytest.mark.django_db
def test_patch_updates_full_name(auth_client):
    response = auth_client.patch(
        "/api/auth/me/", {"full_name": "New Name"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["full_name"] == "New Name"


@pytest.mark.django_db
def test_upload_avatar_clears_default(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    response = auth_client.patch(
        "/api/auth/me/", {"avatar": _png_upload()}, format="multipart"
    )
    assert response.status_code == 200
    assert response.data["avatar"] is not None
    assert response.data["default_avatar"] is None


@pytest.mark.django_db
def test_set_default_clears_uploaded_avatar(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    auth_client.patch("/api/auth/me/", {"avatar": _png_upload()}, format="multipart")
    response = auth_client.patch(
        "/api/auth/me/", {"default_avatar": "quiff"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["default_avatar"] == "quiff"
    assert response.data["avatar"] is None


@pytest.mark.django_db
def test_reject_disallowed_image_type(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    gif = _gif_upload()
    response = auth_client.patch(
        "/api/auth/me/", {"avatar": gif}, format="multipart"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_reject_oversize_image(auth_client, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    response = auth_client.patch(
        "/api/auth/me/", {"avatar": _big_png_over_2mb()}, format="multipart"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_avatar_clears_google_url(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    User.objects.create_user(
        email="g@example.com", full_name="G", password="s3cret-pass-123",
        avatar_url="https://lh3.googleusercontent.com/pic.jpg",
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": "g@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    response = client.patch(
        "/api/auth/me/", {"avatar": _png_upload()}, format="multipart"
    )
    assert response.status_code == 200
    assert response.data["avatar"] is not None
    assert response.data["avatar_url"] is None


@pytest.mark.django_db
def test_set_default_clears_google_url(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    User.objects.create_user(
        email="g2@example.com", full_name="G2", password="s3cret-pass-123",
        avatar_url="https://lh3.googleusercontent.com/pic.jpg",
    )
    client = APIClient()
    client.post(
        "/api/auth/login/",
        {"email": "g2@example.com", "password": "s3cret-pass-123"},
        format="json",
    )
    response = client.patch(
        "/api/auth/me/", {"default_avatar": "quiff"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["default_avatar"] == "quiff"
    assert response.data["avatar_url"] is None


@pytest.mark.django_db
def test_patch_requires_authentication():
    client = APIClient()
    response = client.patch("/api/auth/me/", {"full_name": "X"}, format="json")
    assert response.status_code == 401
