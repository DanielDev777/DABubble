import pytest

from chat.models import Message, Reaction


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


def _add(owner_client, cid, user):
    owner_client.post(
        f"/api/channels/{cid}/add_member/", {"user_id": user.id}, format="json"
    )


@pytest.mark.django_db
def test_message_payload_includes_reactions(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    _add(client, channel["id"], other)
    root = Message.objects.create(
        channel_id=channel["id"], author=owner, content="hi"
    )
    Reaction.objects.create(message=root, user=owner, emoji="👍")
    Reaction.objects.create(message=root, user=other, emoji="👍")
    Reaction.objects.create(message=root, user=owner, emoji="🎉")

    page = client.get(f"/api/messages/?channel={channel['id']}").data
    reactions = page["results"][0]["reactions"]
    assert [r["emoji"] for r in reactions] == ["👍", "🎉"]
    thumbs = reactions[0]
    assert thumbs["count"] == 2
    assert thumbs["reacted"] is True
    assert {u["id"] for u in thumbs["users"]} == {owner.id, other.id}
    party = reactions[1]
    assert party["count"] == 1
    assert party["reacted"] is True


@pytest.mark.django_db
def test_reacted_false_for_non_reactor(make_user, client_for):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    channel = _make_channel(client_for(owner))
    _add(client_for(owner), channel["id"], other)
    root = Message.objects.create(
        channel_id=channel["id"], author=owner, content="hi"
    )
    Reaction.objects.create(message=root, user=owner, emoji="👍")

    page = client_for(other).get(f"/api/messages/?channel={channel['id']}").data
    thumbs = page["results"][0]["reactions"][0]
    assert thumbs["count"] == 1
    assert thumbs["reacted"] is False
