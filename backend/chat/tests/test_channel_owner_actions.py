import pytest

from chat.models import ChannelMembership


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    return owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


@pytest.mark.django_db
def test_non_owner_cannot_add_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    invitee = make_user("invitee@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    response = _add(client_for(member), channel["id"], invitee)
    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_kicks_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    response = client_for(owner).post(
        f"/api/channels/{channel['id']}/kick/", {"user_id": member.id}, format="json"
    )
    assert response.status_code == 204
    assert not ChannelMembership.objects.filter(
        channel_id=channel["id"], user=member
    ).exists()


@pytest.mark.django_db
def test_owner_cannot_kick_self(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    response = client.post(
        f"/api/channels/{channel['id']}/kick/", {"user_id": owner.id}, format="json"
    )
    assert response.status_code == 400
