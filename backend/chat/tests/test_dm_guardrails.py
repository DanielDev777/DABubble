import pytest
from django.contrib.auth import get_user_model

from chat.models import Channel, ChannelMembership

User = get_user_model()


def _make_channel(client, name, description=""):
    return client.post(
        "/api/channels/", {"name": name, "description": description}, format="json"
    )


@pytest.mark.django_db
def test_channel_is_dm_defaults_false():
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    assert channel.is_dm is False


@pytest.mark.django_db
def test_dm_channel_excluded_from_channel_list(make_user, client_for):
    me = make_user("me@example.com")
    dm = Channel.objects.create(name="dm:1:2", owner=me, is_dm=True)
    ChannelMembership.objects.create(channel=dm, user=me)
    names = {c["name"] for c in client_for(me).get("/api/channels/").data}
    assert "dm:1:2" not in names


@pytest.mark.django_db
def test_dm_channel_detail_is_404(make_user, client_for):
    me = make_user("me@example.com")
    dm = Channel.objects.create(name="dm:1:2", owner=me, is_dm=True)
    ChannelMembership.objects.create(channel=dm, user=me)
    assert client_for(me).get(f"/api/channels/{dm.id}/").status_code == 404


@pytest.mark.django_db
def test_channel_name_reserved_dm_prefix_rejected(make_user, client_for):
    me = make_user("me@example.com")
    assert _make_channel(client_for(me), "dm:hack").status_code == 400
    assert _make_channel(client_for(me), "DM:hack").status_code == 400
