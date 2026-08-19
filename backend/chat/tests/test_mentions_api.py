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
