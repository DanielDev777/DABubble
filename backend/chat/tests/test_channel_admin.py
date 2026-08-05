import pytest

from chat.models import Channel


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


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
def test_member_non_owner_cannot_edit(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    channel = _make_channel(client_for(owner))
    client_for(owner).post(
        f"/api/channels/{channel['id']}/add_member/",
        {"user_id": member.id},
        format="json",
    )
    response = client_for(member).patch(
        f"/api/channels/{channel['id']}/", {"name": "Hacked"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_can_delete(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    assert client.delete(f"/api/channels/{channel['id']}/").status_code == 204
    assert not Channel.objects.filter(id=channel["id"]).exists()


@pytest.mark.django_db
def test_non_member_cannot_delete(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    channel = _make_channel(client_for(owner))
    # non-member can't even see it -> 404
    assert client_for(other).delete(f"/api/channels/{channel['id']}/").status_code == 404
