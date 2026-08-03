import pytest

from chat.models import Channel


def _make_channel(client, name="General", is_private=False):
    return client.post(
        "/api/channels/", {"name": name, "is_private": is_private}, format="json"
    ).data


@pytest.mark.django_db
def test_owner_can_edit_name_and_description(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    response = client.patch(
        f"/api/channels/{channel['id']}/",
        {"name": "Renamed", "description": "New desc"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["name"] == "Renamed"
    assert response.data["description"] == "New desc"


@pytest.mark.django_db
def test_non_owner_cannot_edit(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    channel = _make_channel(client_for(owner))  # public -> visible to everyone
    response = client_for(other).patch(
        f"/api/channels/{channel['id']}/", {"name": "Hacked"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_is_private_cannot_be_changed_by_patch(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client, is_private=False)
    response = client.patch(
        f"/api/channels/{channel['id']}/", {"is_private": True}, format="json"
    )
    assert response.status_code == 200
    assert response.data["is_private"] is False


@pytest.mark.django_db
def test_owner_can_delete(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    response = client.delete(f"/api/channels/{channel['id']}/")
    assert response.status_code == 204
    assert not Channel.objects.filter(id=channel["id"]).exists()


@pytest.mark.django_db
def test_non_owner_cannot_delete(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    channel = _make_channel(client_for(owner))
    response = client_for(other).delete(f"/api/channels/{channel['id']}/")
    assert response.status_code == 403
