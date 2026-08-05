import pytest

from chat.models import ChannelMembership


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


@pytest.mark.django_db
def test_owner_adds_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        f"/api/channels/{channel['id']}/add_member/",
        {"user_id": member.id},
        format="json",
    )
    assert response.status_code == 200
    assert ChannelMembership.objects.filter(
        channel_id=channel["id"], user=member
    ).exists()


@pytest.mark.django_db
def test_member_can_leave(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    client_for(owner).post(
        f"/api/channels/{channel['id']}/add_member/",
        {"user_id": member.id}, format="json",
    )
    response = client_for(member).post(
        f"/api/channels/{channel['id']}/leave/", format="json"
    )
    assert response.status_code == 204
    assert not ChannelMembership.objects.filter(
        channel_id=channel["id"], user=member
    ).exists()


@pytest.mark.django_db
def test_owner_cannot_leave(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    response = client.post(f"/api/channels/{channel['id']}/leave/", format="json")
    assert response.status_code == 400
