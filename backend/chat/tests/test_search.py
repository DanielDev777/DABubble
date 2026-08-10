import pytest
from django.contrib.auth import get_user_model

from chat.models import Message

User = get_user_model()


def _emails(results):
    return {u["email"] for u in results}


@pytest.mark.django_db
def test_search_users_by_name_partial(make_user, client_for):
    me = make_user("me@example.com")
    make_user("alice@example.com")  # full_name defaults to "alice"
    make_user("bob@example.com")
    data = client_for(me).get("/api/search/?q=ali").data
    assert "alice@example.com" in _emails(data["users"])
    assert "bob@example.com" not in _emails(data["users"])


@pytest.mark.django_db
def test_search_users_by_email_partial(make_user, client_for):
    me = make_user("me@example.com")
    User.objects.create_user(
        email="zoe@corp.com", full_name="Zoe", password="s3cret-pass-123"
    )
    data = client_for(me).get("/api/search/?q=corp").data
    assert "zoe@corp.com" in _emails(data["users"])


@pytest.mark.django_db
def test_search_excludes_self_and_guests(make_user, client_for):
    me = make_user("findme@example.com")
    User.objects.create_user(
        email="guest_x@guest.local", full_name="findme guest",
        password="s3cret-pass-123", is_guest=True,
    )
    data = client_for(me).get("/api/search/?q=findme").data
    emails = _emails(data["users"])
    assert "findme@example.com" not in emails  # self excluded
    assert "guest_x@guest.local" not in emails  # guest excluded


@pytest.mark.django_db
def test_search_response_has_all_three_keys(make_user, client_for):
    me = make_user("me@example.com")
    data = client_for(me).get("/api/search/?q=x").data
    assert set(data.keys()) == {"users", "channels", "messages"}


def _make_channel(client, name, description=""):
    return client.post(
        "/api/channels/", {"name": name, "description": description}, format="json"
    ).data


@pytest.mark.django_db
def test_search_channels_by_name(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    _make_channel(client, "Alignment")
    _make_channel(client, "Random")
    data = client.get("/api/search/?q=align").data
    names = {c["name"] for c in data["channels"]}
    assert names == {"Alignment"}


@pytest.mark.django_db
def test_search_channels_by_description(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    _make_channel(client, "General", description="team announcements")
    data = client.get("/api/search/?q=announce").data
    assert {c["name"] for c in data["channels"]} == {"General"}


@pytest.mark.django_db
def test_search_excludes_channels_you_are_not_in(make_user, client_for):
    owner = make_user("owner@example.com")
    me = make_user("me@example.com")
    _make_channel(client_for(owner), "SecretPlans")
    data = client_for(me).get("/api/search/?q=secret").data
    assert data["channels"] == []


@pytest.mark.django_db
def test_search_messages_in_your_channel(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    channel = _make_channel(client, "General")
    Message.objects.create(
        channel_id=channel["id"], author=me, content="deploy on friday"
    )
    Message.objects.create(
        channel_id=channel["id"], author=me, content="lunch plans"
    )
    data = client.get("/api/search/?q=deploy").data
    contents = [m["content"] for m in data["messages"]]
    assert contents == ["deploy on friday"]


@pytest.mark.django_db
def test_search_excludes_messages_from_other_channels(make_user, client_for):
    owner = make_user("owner@example.com")
    me = make_user("me@example.com")
    channel = _make_channel(client_for(owner), "Private")
    Message.objects.create(
        channel_id=channel["id"], author=owner, content="secret deploy"
    )
    data = client_for(me).get("/api/search/?q=deploy").data
    assert data["messages"] == []


@pytest.mark.django_db
def test_search_excludes_deleted_messages(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    channel = _make_channel(client, "General")
    msg = Message.objects.create(
        channel_id=channel["id"], author=me, content="deploy secret"
    )
    Message.objects.filter(id=msg.id).update(is_deleted=True)
    data = client.get("/api/search/?q=deploy").data
    assert data["messages"] == []


@pytest.mark.django_db
def test_empty_query_returns_empty_groups(make_user, client_for):
    me = make_user("me@example.com")
    client = client_for(me)
    _make_channel(client, "General")
    data = client.get("/api/search/?q=   ").data
    assert data == {"users": [], "channels": [], "messages": []}
