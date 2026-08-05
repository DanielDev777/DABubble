from unittest.mock import patch

import pytest


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


@pytest.mark.django_db
def test_member_can_post_message(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/", {"channel": channel["id"], "content": "hi"}, format="json"
    )
    assert response.status_code == 201
    assert response.data["content"] == "hi"
    assert response.data["author"]["id"] == owner.id
    assert response.data["is_deleted"] is False


@pytest.mark.django_db
def test_non_member_cannot_post_message_404(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(outsider).post(
        "/api/messages/", {"channel": channel["id"], "content": "hi"}, format="json"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_non_member_cannot_list_messages_404(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(outsider).get(f"/api/messages/?channel={channel['id']}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_list_newest_first_with_cursor(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    for text in ["a", "b", "c"]:
        client.post(
            "/api/messages/", {"channel": channel["id"], "content": text}, format="json"
        )
    page = client.get(f"/api/messages/?channel={channel['id']}&limit=2").data
    assert [m["content"] for m in page["results"]] == ["c", "b"]
    assert page["next"] is not None
    older = client.get(page["next"]).data
    assert [m["content"] for m in older["results"]] == ["a"]


@pytest.mark.django_db
def test_empty_content_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        "/api/messages/", {"channel": channel["id"], "content": "   "}, format="json"
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_post_broadcasts_created(make_user, client_for):
    owner = make_user("owner@example.com")
    channel = _make_channel(client_for(owner))
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client_for(owner).post(
            "/api/messages/", {"channel": channel["id"], "content": "hi"}, format="json"
        )
    assert mock_bc.called
    args = mock_bc.call_args[0]
    assert args[0] == channel["id"]
    assert args[1]["type"] == "message_created"
