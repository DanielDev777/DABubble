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


def _root(client, cid, content="root"):
    return client.post(
        "/api/messages/", {"channel": cid, "content": content}, format="json"
    ).data


@pytest.mark.django_db
def test_post_reply(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    response = client.post(
        "/api/messages/", {"parent": root["id"], "content": "a reply"}, format="json"
    )
    assert response.status_code == 201
    assert response.data["parent"] == root["id"]
    assert response.data["channel"] == channel["id"]
    assert Message.objects.get(id=response.data["id"]).parent_id == root["id"]


@pytest.mark.django_db
def test_cannot_reply_to_a_reply(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    reply = client.post(
        "/api/messages/", {"parent": root["id"], "content": "r"}, format="json"
    ).data
    response = client.post(
        "/api/messages/", {"parent": reply["id"], "content": "nope"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_reply_to_channel_you_are_not_in_404(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    root = _root(client_for(owner), channel["id"])
    response = client_for(outsider).post(
        "/api/messages/", {"parent": root["id"], "content": "x"}, format="json"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_reply_broadcast_includes_parent(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client.post(
            "/api/messages/", {"parent": root["id"], "content": "r"}, format="json"
        )
    payload = mock_bc.call_args[0][1]["message"]
    assert payload["parent"] == root["id"]


@pytest.mark.django_db
def test_reply_can_have_attachment(make_user, client_for, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    response = client.post(
        "/api/messages/",
        {"parent": root["id"], "content": "", "files": [_png()]},
        format="multipart",
    )
    assert response.status_code == 201
    assert len(response.data["attachments"]) == 1
    assert response.data["parent"] == root["id"]
