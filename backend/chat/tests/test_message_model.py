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
def test_message_defaults(channel):
    msg = Message.objects.create(
        channel=channel, author=channel.owner, content="hello"
    )
    assert msg.content == "hello"
    assert msg.is_deleted is False
    assert msg.edited_at is None
    assert msg.created_at is not None
    assert channel.messages.filter(id=msg.id).exists()


@pytest.mark.django_db
def test_messages_ordered_newest_first(channel):
    a = Message.objects.create(channel=channel, author=channel.owner, content="a")
    b = Message.objects.create(channel=channel, author=channel.owner, content="b")
    ids = list(Message.objects.values_list("id", flat=True))
    assert ids == [b.id, a.id]
