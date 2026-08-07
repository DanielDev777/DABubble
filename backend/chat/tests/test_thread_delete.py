from unittest.mock import patch

import pytest

from chat.models import Message


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _root(client, cid, content="root"):
    return client.post(
        "/api/messages/", {"channel": cid, "content": content}, format="json"
    ).data


def _reply(client, parent_id, content="r"):
    return client.post(
        "/api/messages/", {"parent": parent_id, "content": content}, format="json"
    ).data


@pytest.mark.django_db
def test_author_deleting_root_with_replies_soft_deletes(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    reply = _reply(client, root["id"])
    response = client.delete(f"/api/messages/{root['id']}/")
    assert response.status_code == 204
    root_row = Message.objects.get(id=root["id"])
    assert root_row.is_deleted is True
    assert root_row.content == ""
    assert Message.objects.filter(id=reply["id"]).exists()


@pytest.mark.django_db
def test_author_deleting_root_without_replies_hard_deletes(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    response = client.delete(f"/api/messages/{root['id']}/")
    assert response.status_code == 204
    assert not Message.objects.filter(id=root["id"]).exists()


@pytest.mark.django_db
def test_author_deleting_reply_hard_deletes(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    reply = _reply(client, root["id"])
    response = client.delete(f"/api/messages/{reply['id']}/")
    assert response.status_code == 204
    assert not Message.objects.filter(id=reply["id"]).exists()


@pytest.mark.django_db
def test_deleted_broadcast_includes_parent(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = _root(client, channel["id"])
    reply = _reply(client, root["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client.delete(f"/api/messages/{reply['id']}/")
    event = mock_bc.call_args[0][1]
    assert event["type"] == "message_deleted"
    assert event["parent"] == root["id"]
