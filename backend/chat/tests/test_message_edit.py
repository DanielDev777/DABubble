from unittest.mock import patch

import pytest


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


def _post(client, cid, content="hi"):
    return client.post(
        "/api/messages/", {"channel": cid, "content": content}, format="json"
    ).data


@pytest.mark.django_db
def test_author_can_edit(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    msg = _post(client, channel["id"])
    response = client.patch(
        f"/api/messages/{msg['id']}/", {"content": "edited"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["content"] == "edited"
    assert response.data["edited_at"] is not None


@pytest.mark.django_db
def test_non_author_member_cannot_edit(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    msg = _post(client_for(owner), channel["id"])
    response = client_for(member).patch(
        f"/api/messages/{msg['id']}/", {"content": "x"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_edit_broadcasts_updated(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    msg = _post(client, channel["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client.patch(f"/api/messages/{msg['id']}/", {"content": "z"}, format="json")
    assert mock_bc.call_args[0][1]["type"] == "message_updated"
