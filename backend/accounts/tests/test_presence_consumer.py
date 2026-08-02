import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from config.asgi import application

User = get_user_model()


@database_sync_to_async
def make_user(email):
    return User.objects.create_user(
        email=email, full_name="P", password="s3cret-pass-123"
    )


@database_sync_to_async
def conn_count(user_id):
    return User.objects.get(id=user_id).presence_connections


def _headers(user):
    token = str(AccessToken.for_user(user))
    return [(b"cookie", f"{settings.AUTH_COOKIE_ACCESS}={token}".encode())]


async def _connect(user):
    communicator = WebsocketCommunicator(
        application, "/ws/presence/", headers=_headers(user)
    )
    connected, _ = await communicator.connect()
    return communicator, connected


@pytest.mark.django_db(transaction=True)
async def test_authenticated_connect_marks_online_then_offline():
    user = await make_user("a@example.com")
    comm, connected = await _connect(user)
    assert connected is True
    snapshot = await comm.receive_json_from()
    assert snapshot["type"] == "presence.snapshot"
    assert await conn_count(user.id) == 1
    await comm.disconnect()
    assert await conn_count(user.id) == 0


@pytest.mark.django_db(transaction=True)
async def test_anonymous_connection_is_rejected():
    comm = WebsocketCommunicator(application, "/ws/presence/")
    connected, _ = await comm.connect()
    assert connected is False
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_second_tab_keeps_online_until_last_closes():
    user = await make_user("a@example.com")
    comm1, _ = await _connect(user)
    await comm1.receive_json_from()  # snapshot
    comm2, _ = await _connect(user)
    await comm2.receive_json_from()  # snapshot
    assert await conn_count(user.id) == 2
    await comm1.disconnect()
    assert await conn_count(user.id) == 1  # still online
    await comm2.disconnect()
    assert await conn_count(user.id) == 0


@pytest.mark.django_db(transaction=True)
async def test_other_client_receives_online_broadcast():
    listener = await make_user("listener@example.com")
    mover = await make_user("mover@example.com")

    comm_l, _ = await _connect(listener)
    await comm_l.receive_json_from()  # snapshot
    await comm_l.receive_json_from()  # listener's own 0->1 presence.update

    comm_m, _ = await _connect(mover)
    await comm_m.receive_json_from()  # mover's snapshot

    msg = await comm_l.receive_json_from()
    assert msg["type"] == "presence.update"
    assert msg["user_id"] == mover.id
    assert msg["is_online"] is True

    await comm_l.disconnect()
    await comm_m.disconnect()
