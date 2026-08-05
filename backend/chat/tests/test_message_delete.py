from unittest.mock import patch

import pytest

from chat.models import Message


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
def test_author_hard_deletes_own(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    msg = _post(client, channel["id"])
    response = client.delete(f"/api/messages/{msg['id']}/")
    assert response.status_code == 204
    assert not Message.objects.filter(id=msg["id"]).exists()


@pytest.mark.django_db
def test_owner_soft_deletes_members_message(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    msg = _post(client_for(member), channel["id"], "spam")
    response = client_for(owner).delete(f"/api/messages/{msg['id']}/")
    assert response.status_code == 204
    row = Message.objects.get(id=msg["id"])
    assert row.is_deleted is True
    assert row.content == ""


@pytest.mark.django_db
def test_owner_hard_deletes_own(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    msg = _post(client, channel["id"])
    client.delete(f"/api/messages/{msg['id']}/")
    assert not Message.objects.filter(id=msg["id"]).exists()


@pytest.mark.django_db
def test_member_non_author_non_owner_cannot_delete(make_user, client_for):
    owner = make_user("owner@example.com")
    author = make_user("author@example.com")
    bystander = make_user("by@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], author)
    _add(client_for(owner), channel["id"], bystander)
    msg = _post(client_for(author), channel["id"])
    response = client_for(bystander).delete(f"/api/messages/{msg['id']}/")
    assert response.status_code == 403
    assert Message.objects.filter(id=msg["id"]).exists()


@pytest.mark.django_db
def test_author_delete_broadcasts_deleted(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    msg = _post(client, channel["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client.delete(f"/api/messages/{msg['id']}/")
    assert mock_bc.call_args[0][1]["type"] == "message_deleted"


@pytest.mark.django_db
def test_owner_soft_delete_broadcasts_updated(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    msg = _post(client_for(member), channel["id"])
    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        client_for(owner).delete(f"/api/messages/{msg['id']}/")
    assert mock_bc.call_args[0][1]["type"] == "message_updated"
