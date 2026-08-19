import pytest

from chat.models import Channel, ChannelMembership


@pytest.mark.django_db
def test_open_dm_creates_channel(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    response = client_for(me).post("/api/dm/", {"user_id": other.id}, format="json")
    assert response.status_code == 201
    assert response.data["other_user"]["id"] == other.id
    dm = Channel.objects.get(id=response.data["id"])
    assert dm.is_dm is True
    assert dm.members.count() == 2
    assert ChannelMembership.objects.filter(channel=dm, user=me).exists()
    assert ChannelMembership.objects.filter(channel=dm, user=other).exists()


@pytest.mark.django_db
def test_open_dm_is_idempotent(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    first = client_for(me).post("/api/dm/", {"user_id": other.id}, format="json")
    # the other participant opening it from their side returns the same DM
    second = client_for(other).post("/api/dm/", {"user_id": me.id}, format="json")
    assert first.data["id"] == second.data["id"]
    assert second.status_code == 200
    assert Channel.objects.filter(is_dm=True).count() == 1


@pytest.mark.django_db
def test_self_dm(make_user, client_for):
    me = make_user("me@example.com")
    response = client_for(me).post("/api/dm/", {"user_id": me.id}, format="json")
    assert response.status_code == 201
    assert response.data["other_user"]["id"] == me.id
    dm = Channel.objects.get(id=response.data["id"])
    assert dm.members.count() == 1


@pytest.mark.django_db
def test_open_dm_target_404(make_user, client_for):
    me = make_user("me@example.com")
    response = client_for(me).post("/api/dm/", {"user_id": 999999}, format="json")
    assert response.status_code == 404
