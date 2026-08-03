import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from chat.models import Channel, ChannelMembership

User = get_user_model()


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.com", full_name="Owner", password="s3cret-pass-123"
    )


@pytest.mark.django_db
def test_create_channel_with_owner(owner):
    channel = Channel.objects.create(name="General", owner=owner)
    assert channel.name == "General"
    assert channel.owner == owner
    assert channel.is_private is False
    assert channel.description == ""


@pytest.mark.django_db
def test_channel_name_is_unique_case_insensitive(owner):
    Channel.objects.create(name="General", owner=owner)
    with pytest.raises(IntegrityError):
        Channel.objects.create(name="general", owner=owner)


@pytest.mark.django_db
def test_membership_links_user_and_channel(owner):
    channel = Channel.objects.create(name="General", owner=owner)
    ChannelMembership.objects.create(channel=channel, user=owner)
    assert channel.members.filter(id=owner.id).exists()
    assert owner.channels.filter(id=channel.id).exists()
