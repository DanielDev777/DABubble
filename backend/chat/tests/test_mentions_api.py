from unittest.mock import patch

import pytest
from django.db import IntegrityError

from chat.models import Channel, Mention, Message


@pytest.mark.django_db
def test_mention_is_unique_per_message_and_user(make_user):
    author = make_user("author@example.com")
    channel = Channel.objects.create(name="General", owner=author)
    message = Message.objects.create(
        channel=channel, author=author, content="hi @Author"
    )
    Mention.objects.create(message=message, user=author)
    with pytest.raises(IntegrityError):
        Mention.objects.create(message=message, user=author)


@pytest.mark.django_db
def test_mentions_are_reachable_from_the_message(make_user):
    author = make_user("author@example.com")
    channel = Channel.objects.create(name="General", owner=author)
    message = Message.objects.create(channel=channel, author=author, content="hi")
    Mention.objects.create(message=message, user=author)
    assert message.mentions.count() == 1
    assert message.mentions.first().user_id == author.id


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
    )


@pytest.mark.django_db
def test_mention_is_recorded_and_returned(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)

    response = _post(owner_client, channel["id"], "hey @Noah Braun look")

    assert response.status_code == 201
    assert response.data["mentions"] == [{"id": noah.id, "full_name": "Noah Braun"}]
    assert Mention.objects.filter(message_id=response.data["id"]).count() == 1


@pytest.mark.django_db
def test_non_member_name_is_ignored(make_user, client_for):
    owner = make_user("owner@example.com")
    _named(make_user, "outsider@example.com", "Elise Roth")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)

    response = _post(owner_client, channel["id"], "hey @Elise Roth")

    assert response.data["mentions"] == []
    assert Mention.objects.count() == 0


@pytest.mark.django_db
def test_self_mention_is_recorded(make_user, client_for):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)

    response = _post(owner_client, channel["id"], "note to @Ada Owner")

    assert response.data["mentions"] == [{"id": owner.id, "full_name": "Ada Owner"}]


@pytest.mark.django_db
def test_mention_in_a_dm_resolves_the_participant(make_user, client_for):
    me = make_user("me@example.com")
    other = _named(make_user, "other@example.com", "Sofia Mueller")
    client = client_for(me)
    dm = client.post("/api/dm/", {"user_id": other.id}, format="json").data

    response = _post(client, dm["id"], "hi @Sofia Mueller")

    assert response.data["mentions"] == [{"id": other.id, "full_name": "Sofia Mueller"}]


@pytest.mark.django_db
def test_soft_deleted_message_reports_no_mentions(make_user, client_for):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    msg = _post(owner_client, channel["id"], "ping @Ada Owner").data

    message = Message.objects.get(pk=msg["id"])
    message.is_deleted = True
    message.save(update_fields=["is_deleted"])

    listing = owner_client.get(f"/api/messages/?channel={channel['id']}").data
    assert listing["results"][0]["mentions"] == []


@pytest.mark.django_db
def test_edit_adds_a_mention(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "no names here").data

    response = owner_client.patch(
        f"/api/messages/{msg['id']}/", {"content": "now @Noah Braun"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["mentions"] == [{"id": noah.id, "full_name": "Noah Braun"}]


@pytest.mark.django_db
def test_edit_removes_a_mention(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun").data

    response = owner_client.patch(
        f"/api/messages/{msg['id']}/", {"content": "never mind"}, format="json"
    )

    assert response.data["mentions"] == []
    assert Mention.objects.filter(message_id=msg["id"]).count() == 0


@pytest.mark.django_db
def test_edit_keeps_the_row_of_an_unchanged_mention(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    sofia = _named(make_user, "sofia@example.com", "Sofia Mueller")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    _add(owner_client, channel["id"], sofia)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun").data
    row_id = Mention.objects.get(message_id=msg["id"], user=noah).id

    owner_client.patch(
        f"/api/messages/{msg['id']}/",
        {"content": "hey @Noah Braun and @Sofia Mueller"},
        format="json",
    )

    assert Mention.objects.get(message_id=msg["id"], user=noah).id == row_id
    assert Mention.objects.filter(message_id=msg["id"]).count() == 2


@pytest.mark.django_db
def test_hard_delete_removes_mentions(make_user, client_for):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    msg = _post(owner_client, channel["id"], "ping @Ada Owner").data

    owner_client.delete(f"/api/messages/{msg['id']}/")

    assert Mention.objects.count() == 0


@pytest.mark.django_db
def test_soft_delete_clears_mentions(make_user, client_for):
    owner = _named(make_user, "owner@example.com", "Ada Owner")
    member = make_user("member@example.com")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], member)
    msg = _post(owner_client, channel["id"], "ping @Ada Owner").data
    # A reply forces the soft-delete path instead of the hard delete.
    client_for(member).post(
        "/api/messages/", {"parent": msg["id"], "content": "re"}, format="json"
    )

    owner_client.delete(f"/api/messages/{msg['id']}/")

    message = Message.objects.get(pk=msg["id"])
    assert message.is_deleted is True
    assert Mention.objects.filter(message=message).count() == 0


@pytest.mark.django_db
def test_broadcast_payload_carries_mentions(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)

    with patch("chat.api.views.broadcast_to_channel") as mock_bc:
        _post(owner_client, channel["id"], "hey @Noah Braun")

    payload = mock_bc.call_args[0][1]
    assert payload["type"] == "message_created"
    assert payload["message"]["mentions"] == [
        {"id": noah.id, "full_name": "Noah Braun"}
    ]


@pytest.mark.django_db
def test_removing_a_member_leaves_old_mentions_intact(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun").data

    owner_client.post(
        f"/api/channels/{channel['id']}/kick/", {"user_id": noah.id}, format="json"
    )

    assert Mention.objects.filter(message_id=msg["id"], user=noah).count() == 1


@pytest.mark.django_db
def test_feed_does_not_regress_into_n_plus_one(
    make_user, client_for, django_assert_max_num_queries
):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    for i in range(5):
        _post(owner_client, channel["id"], f"msg {i} for @Noah Braun")

    with django_assert_max_num_queries(12):
        owner_client.get(f"/api/messages/?channel={channel['id']}")
