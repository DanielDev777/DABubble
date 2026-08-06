import pytest
from django.contrib.auth import get_user_model

from chat.models import Channel, Message

User = get_user_model()


@pytest.fixture
def channel(db):
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    return Channel.objects.create(name="General", owner=owner)


@pytest.mark.django_db
def test_root_has_no_parent(channel):
    root = Message.objects.create(channel=channel, author=channel.owner, content="root")
    assert root.parent is None
    assert root.replies.count() == 0


@pytest.mark.django_db
def test_reply_links_to_parent(channel):
    root = Message.objects.create(channel=channel, author=channel.owner, content="root")
    reply = Message.objects.create(
        channel=channel, author=channel.owner, content="reply", parent=root
    )
    assert reply.parent_id == root.id
    assert list(root.replies.all()) == [reply]
