import pytest
from django.contrib.auth import get_user_model

from chat.models import Channel

User = get_user_model()


@pytest.mark.django_db
def test_channel_is_demo_defaults_false():
    owner = User.objects.create_user(
        email="o@example.com", full_name="O", password="s3cret-pass-123"
    )
    channel = Channel.objects.create(name="General", owner=owner)
    assert channel.is_demo is False
