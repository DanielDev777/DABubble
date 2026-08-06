import io
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from chat.models import Message


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _png(name="a.png"):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


@pytest.fixture(autouse=True)
def _media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.mark.django_db
def test_post_message_with_one_image(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "content": "look", "files": [_png()]},
        format="multipart",
    )
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    att = response.data["attachments"][0]
    assert att["content_type"] == "image/png"
    assert att["file"].startswith("http")


@pytest.mark.django_db
def test_post_message_with_multiple_files(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "content": "", "files": [_png("a.png"), _png("b.png")]},
        format="multipart",
    )
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 2


@pytest.mark.django_db
def test_files_only_message_ok(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "files": [_png()]},
        format="multipart",
    )
    assert response.status_code == 201
    assert response.data["content"] == ""


@pytest.mark.django_db
def test_neither_text_nor_files_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/", {"channel": channel["id"], "content": "  "}, format="multipart"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_disallowed_type_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    bad = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "files": [bad]},
        format="multipart",
    )
    assert response.status_code == 400
    assert not Message.objects.exists()


@pytest.mark.django_db
def test_oversize_file_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    big = SimpleUploadedFile(
        "big.png", b"\0" * (10 * 1024 * 1024 + 1), content_type="image/png"
    )
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "files": [big]},
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_too_many_files_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    files = [_png(f"{i}.png") for i in range(11)]
    response = client_for(owner).post(
        "/api/messages/",
        {"channel": channel["id"], "files": files},
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_broadcast_includes_attachments(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client_for(owner).post(
            "/api/messages/",
            {"channel": channel["id"], "content": "x", "files": [_png()]},
            format="multipart",
        )
    payload = mock_bc.call_args[0][1]["message"]
    assert len(payload["attachments"]) == 1
