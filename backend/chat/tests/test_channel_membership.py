import pytest

from chat.models import ChannelMembership


def _make_channel(client, name="General", is_private=False):
    return client.post(
        "/api/channels/", {"name": name, "is_private": is_private}, format="json"
    ).data


@pytest.mark.django_db
def test_join_public_channel(make_user, client_for):
    owner = make_user("owner@example.com")
    joiner = make_user("joiner@example.com")
    channel = _make_channel(client_for(owner), "Public1")
    response = client_for(joiner).post(f"/api/channels/{channel['id']}/join/", format="json")
    assert response.status_code == 200
    assert response.data["is_member"] is True


@pytest.mark.django_db
def test_join_private_channel_forbidden(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner), "Secret", is_private=True)
    response = client_for(outsider).post(f"/api/channels/{channel['id']}/join/", format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_double_join_rejected(make_user, client_for):
    owner = make_user("owner@example.com")
    joiner = make_user("joiner@example.com")
    channel = _make_channel(client_for(owner), "Public1")
    jclient = client_for(joiner)
    jclient.post(f"/api/channels/{channel['id']}/join/", format="json")
    response = jclient.post(f"/api/channels/{channel['id']}/join/", format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_member_can_leave(make_user, client_for):
    owner = make_user("owner@example.com")
    joiner = make_user("joiner@example.com")
    channel = _make_channel(client_for(owner), "Public1")
    jclient = client_for(joiner)
    jclient.post(f"/api/channels/{channel['id']}/join/", format="json")
    response = jclient.post(f"/api/channels/{channel['id']}/leave/", format="json")
    assert response.status_code == 204
    assert not ChannelMembership.objects.filter(
        channel_id=channel["id"], user=joiner
    ).exists()


@pytest.mark.django_db
def test_owner_cannot_leave(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client, "Public1")
    response = client.post(f"/api/channels/{channel['id']}/leave/", format="json")
    assert response.status_code == 400
