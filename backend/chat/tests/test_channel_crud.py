import pytest

from chat.models import Channel


@pytest.mark.django_db
def test_create_channel_makes_owner_a_member(make_user, client_for):
    user = make_user("a@example.com")
    client = client_for(user)
    response = client.post(
        "/api/channels/",
        {"name": "General", "description": "Talk", "is_private": False},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["name"] == "General"
    assert response.data["owner"]["id"] == user.id
    assert response.data["is_member"] is True
    assert response.data["member_count"] == 1
    channel = Channel.objects.get(id=response.data["id"])
    assert channel.members.filter(id=user.id).exists()


@pytest.mark.django_db
def test_duplicate_name_case_insensitive_rejected(make_user, client_for):
    user = make_user("a@example.com")
    client = client_for(user)
    client.post("/api/channels/", {"name": "General"}, format="json")
    response = client.post("/api/channels/", {"name": "general"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_list_shows_public_hides_private_from_non_members(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    oclient = client_for(owner)
    oclient.post("/api/channels/", {"name": "Public1", "is_private": False}, format="json")
    oclient.post("/api/channels/", {"name": "Secret", "is_private": True}, format="json")

    names = {c["name"] for c in client_for(other).get("/api/channels/").data}
    assert "Public1" in names
    assert "Secret" not in names


@pytest.mark.django_db
def test_retrieve_private_as_non_member_is_404(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    created = client_for(owner).post(
        "/api/channels/", {"name": "Secret", "is_private": True}, format="json"
    )
    cid = created.data["id"]
    response = client_for(other).get(f"/api/channels/{cid}/")
    assert response.status_code == 404
