import pytest

from chat.models import ChannelMembership


def _make_channel(client, name="General", is_private=False):
    return client.post(
        "/api/channels/", {"name": name, "is_private": is_private}, format="json"
    ).data


@pytest.mark.django_db
def test_owner_adds_member_to_private_channel(make_user, client_for):
    owner = make_user("owner@example.com")
    invitee = make_user("invitee@example.com")
    channel = _make_channel(client_for(owner), "Secret", is_private=True)
    response = client_for(owner).post(
        f"/api/channels/{channel['id']}/add_member/",
        {"user_id": invitee.id},
        format="json",
    )
    assert response.status_code == 200
    assert ChannelMembership.objects.filter(
        channel_id=channel["id"], user=invitee
    ).exists()


@pytest.mark.django_db
def test_non_owner_cannot_add_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    invitee = make_user("invitee@example.com")
    channel = _make_channel(client_for(owner), "Public1")
    client_for(member).post(f"/api/channels/{channel['id']}/join/", format="json")
    response = client_for(member).post(
        f"/api/channels/{channel['id']}/add_member/",
        {"user_id": invitee.id},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_kicks_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner), "Public1")
    client_for(member).post(f"/api/channels/{channel['id']}/join/", format="json")
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
    channel = _make_channel(client, "Public1")
    response = client.post(
        f"/api/channels/{channel['id']}/kick/", {"user_id": owner.id}, format="json"
    )
    assert response.status_code == 400
