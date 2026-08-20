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
