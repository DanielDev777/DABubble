import pytest

from chat.models import Message


def _make_channel(client, name="General"):
    return client.post("/api/channels/", {"name": name}, format="json").data


@pytest.mark.django_db
def test_feed_excludes_replies(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = Message.objects.create(
        channel_id=channel["id"], author=owner, content="root"
    )
    Message.objects.create(
        channel_id=channel["id"], author=owner, content="reply", parent=root
    )
    page = client.get(f"/api/messages/?channel={channel['id']}").data
    contents = [m["content"] for m in page["results"]]
    assert contents == ["root"]
    assert page["results"][0]["reply_count"] == 1
    assert page["results"][0]["last_reply_at"] is not None


@pytest.mark.django_db
def test_thread_lists_replies_oldest_first(make_user, client_for):
    owner = make_user("owner@example.com")
    client = client_for(owner)
    channel = _make_channel(client)
    root = Message.objects.create(
        channel_id=channel["id"], author=owner, content="root"
    )
    for text in ["r1", "r2", "r3"]:
        Message.objects.create(
            channel_id=channel["id"], author=owner, content=text, parent=root
        )
    page = client.get(f"/api/messages/?parent={root.id}").data
    assert [m["content"] for m in page["results"]] == ["r1", "r2", "r3"]
    assert all(m["parent"] == root.id for m in page["results"])


@pytest.mark.django_db
def test_thread_non_member_404(make_user, client_for):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    channel = _make_channel(client_for(owner))
    root = Message.objects.create(
        channel_id=channel["id"], author=owner, content="root"
    )
    response = client_for(outsider).get(f"/api/messages/?parent={root.id}")
    assert response.status_code == 404
