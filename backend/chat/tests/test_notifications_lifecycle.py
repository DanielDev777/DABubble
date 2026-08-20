import pytest
from django.db import IntegrityError

from chat.models import Channel, Message, Notification


@pytest.mark.django_db
def test_notification_is_unique_per_user_and_message(make_user):
    author = make_user("author@example.com")
    channel = Channel.objects.create(name="General", owner=author)
    message = Message.objects.create(channel=channel, author=author, content="hi")
    Notification.objects.create(
        user=author, message=message, kind=Notification.MENTION
    )
    with pytest.raises(IntegrityError):
        Notification.objects.create(
            user=author, message=message, kind=Notification.DM
        )


@pytest.mark.django_db
def test_notification_defaults_to_unread(make_user):
    author = make_user("author@example.com")
    channel = Channel.objects.create(name="General", owner=author)
    message = Message.objects.create(channel=channel, author=author, content="hi")
    note = Notification.objects.create(
        user=author, message=message, kind=Notification.REPLY
    )
    assert note.is_read is False
    assert note.created_at is not None
    assert author.notifications.count() == 1


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


def _named(make_user, email, full_name):
    user = make_user(email)
    user.full_name = full_name
    user.save(update_fields=["full_name"])
    return user


def _post(client, cid, content):
    return client.post(
        "/api/messages/", {"channel": cid, "content": content}, format="json"
    ).data


@pytest.mark.django_db
def test_editing_in_a_mention_creates_a_notification(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "no names here")
    assert Notification.objects.count() == 0

    owner_client.patch(
        f"/api/messages/{msg['id']}/", {"content": "now @Noah Braun"}, format="json"
    )

    assert Notification.objects.get(user=noah).kind == Notification.MENTION


@pytest.mark.django_db
def test_editing_out_a_mention_deletes_the_notification(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun")

    owner_client.patch(
        f"/api/messages/{msg['id']}/", {"content": "never mind"}, format="json"
    )

    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_editing_out_a_mention_in_a_dm_downgrades_instead_of_deleting(
    make_user, client_for
):
    me = make_user("me@example.com")
    other = _named(make_user, "other@example.com", "Noah Braun")
    client = client_for(me)
    dm = client.post("/api/dm/", {"user_id": other.id}, format="json").data
    msg = _post(client, dm["id"], "hi @Noah Braun")
    row_id = Notification.objects.get(user=other).id

    client.patch(f"/api/messages/{msg['id']}/", {"content": "hi"}, format="json")

    note = Notification.objects.get(user=other)
    assert note.id == row_id
    assert note.kind == Notification.DM


@pytest.mark.django_db
def test_a_surviving_row_keeps_its_read_state(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun")
    Notification.objects.filter(user=noah).update(is_read=True)

    owner_client.patch(
        f"/api/messages/{msg['id']}/",
        {"content": "hey @Noah Braun, again"},
        format="json",
    )

    assert Notification.objects.get(user=noah).is_read is True


@pytest.mark.django_db
def test_hard_delete_removes_notifications(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun")

    owner_client.delete(f"/api/messages/{msg['id']}/")

    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_soft_delete_clears_notifications(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun")
    # A reply forces the soft-delete path instead of the hard delete.
    client_for(noah).post(
        "/api/messages/", {"parent": msg["id"], "content": "re"}, format="json"
    )
    Notification.objects.filter(message__parent_id=msg["id"]).delete()

    owner_client.delete(f"/api/messages/{msg['id']}/")

    assert Notification.objects.filter(message_id=msg["id"]).count() == 0
