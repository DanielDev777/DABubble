from unittest.mock import patch

import pytest

from chat.models import Message, Reaction


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _root(client, cid, content="root"):
    return client.post(
        "/api/messages/", {"channel": cid, "content": content}, format="json"
    ).data


def _reactions(data, emoji):
    for r in data["reactions"]:
        if r["emoji"] == emoji:
            return r
    return None


@pytest.mark.django_db
def test_react_adds(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    response = client.post(
        f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json"
    )
    assert response.status_code == 200
    thumbs = _reactions(response.data, "👍")
    assert thumbs["count"] == 1
    assert thumbs["reacted"] is True


@pytest.mark.django_db
def test_react_again_removes(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    client.post(f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json")
    response = client.post(
        f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json"
    )
    assert response.status_code == 200
    assert _reactions(response.data, "👍") is None
    assert not Reaction.objects.filter(message_id=root["id"]).exists()


@pytest.mark.django_db
def test_different_emojis_stack(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    client.post(f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json")
    response = client.post(
        f"/api/messages/{root['id']}/react/", {"emoji": "🎉"}, format="json"
    )
    emojis = {r["emoji"] for r in response.data["reactions"]}
    assert emojis == {"👍", "🎉"}


@pytest.mark.django_db
def test_invalid_emoji_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    response = client.post(
        f"/api/messages/{root['id']}/react/", {"emoji": "🦄"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_non_member_cannot_react_404(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    root = _root(client_for(owner), channel["id"])
    response = client_for(outsider).post(
        f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_cannot_react_to_deleted(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    Message.objects.filter(id=root["id"]).update(is_deleted=True)
    response = client.post(
        f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_react_broadcasts_updated(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client.post(f"/api/messages/{root['id']}/react/", {"emoji": "👍"}, format="json")
    assert mock_bc.call_args[0][1]["type"] == "message_updated"


@pytest.mark.django_db
def test_can_react_to_a_reply(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    reply = client.post(
        "/api/messages/", {"parent": root["id"], "content": "r"}, format="json"
    ).data
    response = client.post(
        f"/api/messages/{reply['id']}/react/", {"emoji": "❤️"}, format="json"
    )
    assert response.status_code == 200
    assert _reactions(response.data, "❤️")["count"] == 1
