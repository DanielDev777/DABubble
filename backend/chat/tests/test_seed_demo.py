import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from chat.models import Channel, Message, Reaction

User = get_user_model()


@pytest.mark.django_db
def test_seed_creates_demo_workspace():
    call_command("seed_demo")
    assert User.objects.filter(email__endswith="@demo.local").count() >= 5
    demo_channels = Channel.objects.filter(is_demo=True)
    assert demo_channels.count() == 3
    for channel in demo_channels:
        assert channel.messages.exists()
    # at least one thread (a message with a parent)
    assert Message.objects.filter(parent__isnull=False).exists()
    # at least one reaction
    assert Reaction.objects.exists()


@pytest.mark.django_db
def test_seed_is_idempotent():
    call_command("seed_demo")
    users = User.objects.count()
    channels = Channel.objects.count()
    messages = Message.objects.count()
    reactions = Reaction.objects.count()

    call_command("seed_demo")
    assert User.objects.count() == users
    assert Channel.objects.count() == channels
    assert Message.objects.count() == messages
    assert Reaction.objects.count() == reactions


@pytest.mark.django_db
def test_demo_users_cannot_log_in():
    call_command("seed_demo")
    user = User.objects.filter(email__endswith="@demo.local").first()
    assert not user.has_usable_password()
