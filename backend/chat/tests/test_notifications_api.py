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


@pytest.mark.django_db
def test_list_returns_your_own_rows_with_context(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client, "Entwicklerteam")
    _add(owner_client, channel["id"], noah)
    msg = _post(owner_client, channel["id"], "hey @Noah Braun")

    listing = client_for(noah).get("/api/notifications/").data

    assert len(listing["results"]) == 1
    row = listing["results"][0]
    assert row["kind"] == "mention"
    assert row["is_read"] is False
    assert row["channel"] == {
        "id": channel["id"],
        "name": "Entwicklerteam",
        "is_dm": False,
    }
    assert row["message"]["id"] == msg["id"]
    assert row["message"]["content"] == "hey @Noah Braun"
    assert row["message"]["author"]["id"] == owner.id


@pytest.mark.django_db
def test_list_never_leaks_another_users_rows(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    _post(owner_client, channel["id"], "hey @Noah Braun")

    assert client_for(owner).get("/api/notifications/").data["results"] == []


@pytest.mark.django_db
def test_list_is_newest_first(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    _post(owner_client, channel["id"], "first @Noah Braun")
    second = _post(owner_client, channel["id"], "second @Noah Braun")

    listing = client_for(noah).get("/api/notifications/").data

    assert listing["results"][0]["message"]["id"] == second["id"]


@pytest.mark.django_db
def test_unread_filter(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    channel = _make_channel(owner_client)
    _add(owner_client, channel["id"], noah)
    _post(owner_client, channel["id"], "one @Noah Braun")
    _post(owner_client, channel["id"], "two @Noah Braun")
    Notification.objects.filter(user=noah).update(is_read=True)
    _post(owner_client, channel["id"], "three @Noah Braun")

    listing = client_for(noah).get("/api/notifications/?unread=true").data

    assert len(listing["results"]) == 1
    assert listing["results"][0]["message"]["content"] == "three @Noah Braun"


@pytest.mark.django_db
def test_summary_counts_unread_per_channel(make_user, client_for):
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    first = _make_channel(owner_client, "One")
    second = _make_channel(owner_client, "Two")
    _add(owner_client, first["id"], noah)
    _add(owner_client, second["id"], noah)
    _post(owner_client, first["id"], "a @Noah Braun")
    _post(owner_client, second["id"], "b @Noah Braun")
    _post(owner_client, second["id"], "c @Noah Braun")

    summary = client_for(noah).get("/api/notifications/summary/").data

    assert summary["unread_total"] == 3
    assert summary["by_channel"] == {str(first["id"]): 1, str(second["id"]): 2}


def _two_channels_with_mentions(make_user, client_for):
    """Return (noah, noah_client, first_channel, second_channel) with 1 + 2 unread."""
    owner = make_user("owner@example.com")
    noah = _named(make_user, "noah@example.com", "Noah Braun")
    owner_client = client_for(owner)
    first = _make_channel(owner_client, "One")
    second = _make_channel(owner_client, "Two")
    _add(owner_client, first["id"], noah)
    _add(owner_client, second["id"], noah)
    _post(owner_client, first["id"], "a @Noah Braun")
    _post(owner_client, second["id"], "b @Noah Braun")
    _post(owner_client, second["id"], "c @Noah Braun")
    return noah, client_for(noah), first, second


@pytest.mark.django_db
def test_mark_read_by_ids(make_user, client_for):
    noah, noah_client, _, _ = _two_channels_with_mentions(make_user, client_for)
    target = Notification.objects.filter(user=noah).first()

    response = noah_client.post(
        "/api/notifications/read/", {"ids": [target.id]}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {"marked": 1, "unread_total": 2}
    target.refresh_from_db()
    assert target.is_read is True


@pytest.mark.django_db
def test_mark_read_by_channel(make_user, client_for):
    noah, noah_client, _, second = _two_channels_with_mentions(make_user, client_for)

    response = noah_client.post(
        "/api/notifications/read/", {"channel": second["id"]}, format="json"
    )

    assert response.data == {"marked": 2, "unread_total": 1}
    assert (
        Notification.objects.filter(
            user=noah, message__channel_id=second["id"], is_read=False
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_mark_read_all(make_user, client_for):
    noah, noah_client, _, _ = _two_channels_with_mentions(make_user, client_for)

    response = noah_client.post(
        "/api/notifications/read/", {"all": True}, format="json"
    )

    assert response.data == {"marked": 3, "unread_total": 0}


@pytest.mark.django_db
def test_marking_an_already_read_row_is_a_no_op(make_user, client_for):
    noah, noah_client, _, _ = _two_channels_with_mentions(make_user, client_for)
    target = Notification.objects.filter(user=noah).first()
    noah_client.post("/api/notifications/read/", {"ids": [target.id]}, format="json")

    response = noah_client.post(
        "/api/notifications/read/", {"ids": [target.id]}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {"marked": 0, "unread_total": 2}


@pytest.mark.django_db
def test_empty_or_ambiguous_body_is_rejected(make_user, client_for):
    _, noah_client, first, _ = _two_channels_with_mentions(make_user, client_for)

    assert noah_client.post(
        "/api/notifications/read/", {}, format="json"
    ).status_code == 400
    assert noah_client.post(
        "/api/notifications/read/",
        {"all": True, "channel": first["id"]},
        format="json",
    ).status_code == 400


@pytest.mark.django_db
def test_another_users_ids_are_ignored(make_user, client_for):
    noah, _, _, _ = _two_channels_with_mentions(make_user, client_for)
    stranger = make_user("stranger@example.com")
    theirs = Notification.objects.filter(user=noah).first()

    response = client_for(stranger).post(
        "/api/notifications/read/", {"ids": [theirs.id]}, format="json"
    )

    assert response.data == {"marked": 0, "unread_total": 0}
    theirs.refresh_from_db()
    assert theirs.is_read is False
