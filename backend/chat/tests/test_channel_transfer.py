import pytest

from chat.models import Channel, ChannelMembership


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    return owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


@pytest.mark.django_db
def test_owner_transfers_to_member(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    response = client_for(owner).post(
        f"/api/channels/{channel['id']}/transfer/",
        {"user_id": member.id}, format="json",
    )
    assert response.status_code == 200
    assert response.data["owner"]["id"] == member.id
    updated = Channel.objects.get(id=channel["id"])
    assert updated.owner_id == member.id
    assert ChannelMembership.objects.filter(channel=updated, user=owner).exists()


@pytest.mark.django_db
def test_transfer_to_non_member_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    stranger = make_user("stranger@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(owner).post(
        f"/api/channels/{channel['id']}/transfer/",
        {"user_id": stranger.id}, format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_members_endpoint_lists_cards(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], member)
    response = client_for(owner).get(f"/api/channels/{channel['id']}/members/")
    assert response.status_code == 200
    emails = {u["email"] for u in response.data}
    assert emails == {"owner@example.com", "member@example.com"}


@pytest.mark.django_db
def test_members_hidden_for_non_member(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(outsider).get(f"/api/channels/{channel['id']}/members/")
    assert response.status_code == 404
