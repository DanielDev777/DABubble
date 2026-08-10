import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from chat.models import Channel, Message, Reaction

User = get_user_model()


@pytest.fixture
def message(db):
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    return Message.objects.create(channel=channel, author=owner, content="hi")


@pytest.mark.django_db
def test_reaction_links_to_message(message):
    r = Reaction.objects.create(message=message, user=message.author, emoji="👍")
    assert message.reactions.filter(id=r.id).exists()
    assert r.emoji == "👍"


@pytest.mark.django_db
def test_reaction_unique_per_user_emoji_message(message):
    Reaction.objects.create(message=message, user=message.author, emoji="👍")
    with pytest.raises(IntegrityError):
        Reaction.objects.create(message=message, user=message.author, emoji="👍")


@pytest.mark.django_db
def test_same_user_different_emoji_allowed(message):
    Reaction.objects.create(message=message, user=message.author, emoji="👍")
    Reaction.objects.create(message=message, user=message.author, emoji="🎉")
    assert message.reactions.count() == 2
