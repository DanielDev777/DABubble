import pytest

from chat.models import Notification


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


def _reply(client, parent_id, content):
    return client.post(
        "/api/messages/", {"parent": parent_id, "content": content}, format="json"
    ).data


@pytest.mark.django_db
def test_mention_notifies_the_mentioned_member(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)

    _post(owner_client, channel["id"], "hey @Noah Braun")

    note = Notification.objects.get(user=noah)
    assert note.kind == Notification.MENTION
    assert note.is_read is False


@pytest.mark.django_db
def test_self_mention_notifies_nobody(make_user, client_for):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)

    _post(owner_client, channel["id"], "note to @Ada Owner")

    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_plain_channel_message_notifies_nobody(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], member)

    _post(owner_client, channel["id"], "morning everyone")

    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_dm_message_notifies_the_other_participant(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    client = client_for(me)
    dm = client.post("/api/dm/", {"user_id": other.id}, format="json").data

    _post(client, dm["id"], "hey")

    note = Notification.objects.get()
    assert note.user_id == other.id
    assert note.kind == Notification.DM


@pytest.mark.django_db
def test_self_dm_notifies_nobody(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    dm = client.post("/api/dm/", {"user_id": me.id}, format="json").data

    _post(client, dm["id"], "note to self")

    assert Notification.objects.count() == 0


@pytest.mark.django_db
def test_reply_notifies_the_root_author(make_user, client_for):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], member)
    root = _post(owner_client, channel["id"], "question")

    _reply(client_for(member), root["id"], "an answer")

    note = Notification.objects.get(user=owner)
    assert note.kind == Notification.REPLY


@pytest.mark.django_db
def test_reply_notifies_earlier_repliers_but_not_the_poster(make_user, client_for):
    owner = make_user("owner@example.com")
    first = make_user("first@example.com")
    second = make_user("second@example.com")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], first)
    _add(owner_client, channel["id"], second)
    root = _post(owner_client, channel["id"], "question")
    _reply(client_for(first), root["id"], "first answer")

    _reply(client_for(second), root["id"], "second answer")

    notified = set(
        Notification.objects.filter(message__parent_id=root["id"])
        .values_list("user_id", flat=True)
    )
    assert owner.id in notified
    assert first.id in notified
    assert second.id not in notified


@pytest.mark.django_db
def test_dm_that_mentions_you_yields_one_row_labelled_mention(make_user, client_for):
    me = make_user("me@example.com")
    other = _named(make_user, "other@example.com", "Noah Braun")
    client = client_for(me)
    dm = client.post("/api/dm/", {"user_id": other.id}, format="json").data

    _post(client, dm["id"], "hi @Noah Braun")

    note = Notification.objects.get(user=other)
    assert note.kind == Notification.MENTION
    assert Notification.objects.count() == 1


@pytest.mark.django_db
def test_reply_that_mentions_the_root_author_is_labelled_mention(
    make_user, client_for
):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    member = make_user("member@example.com")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], member)
    root = _post(owner_client, channel["id"], "question")

    _reply(client_for(member), root["id"], "see @Ada Owner")

    note = Notification.objects.get(user=owner)
    assert note.kind == Notification.MENTION
