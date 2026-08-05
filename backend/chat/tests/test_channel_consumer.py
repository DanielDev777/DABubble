import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from chat.models import Channel, ChannelMembership
from config.asgi import application

User = get_user_model()


@database_sync_to_async
def make_channel_with_member(owner_email, member_email=None):
    owner = User.objects.create_user(
        email=owner_email, full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    ChannelMembership.objects.create(channel=channel, user=owner)
    member = None
    if member_email:
        member = User.objects.create_user(
            email=member_email, full_name="M", password="s3cret-pass-123"
        )
        ChannelMembership.objects.create(channel=channel, user=member)
    return channel, owner, member


def _headers(user):
    token = str(AccessToken.for_user(user))
    return [(b"cookie", f"{settings.AUTH_COOKIE_ACCESS}={token}".encode())]


async def _connect(channel_id, user):
    comm = WebsocketCommunicator(
        application, f"/ws/channel/{channel_id}/", headers=_headers(user)
    )
    connected, _ = await comm.connect()
    return comm, connected


@pytest.mark.django_db(transaction=True)
async def test_member_can_connect():
    channel, owner, _ = await make_channel_with_member("o@example.com")
    comm, connected = await _connect(channel.id, owner)
    assert connected is True
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_non_member_rejected():
    channel, owner, _ = await make_channel_with_member("o@example.com")
    outsider = await database_sync_to_async(User.objects.create_user)(
        email="out@example.com", full_name="X", password="s3cret-pass-123"
    )
    comm, connected = await _connect(channel.id, outsider)
    assert connected is False
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_broadcast_reaches_connected_member():
    channel, owner, _ = await make_channel_with_member("o@example.com")
    comm, connected = await _connect(channel.id, owner)
    assert connected is True
    layer = get_channel_layer()
    await layer.group_send(
        f"channel_{channel.id}",
        {"type": "message_created", "message": {"id": 1, "content": "hi"}},
    )
    event = await comm.receive_json_from()
    assert event["type"] == "message.created"
    assert event["message"]["content"] == "hi"
    await comm.disconnect()
