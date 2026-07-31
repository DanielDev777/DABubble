import pytest
from django.contrib.auth import get_user_model

from accounts.api.serializers import UserSerializer

User = get_user_model()


@pytest.mark.django_db
def test_new_user_is_offline():
    user = User.objects.create_user(
        email="p@example.com", full_name="P", password="s3cret-pass-123"
    )
    assert user.presence_connections == 0
    assert user.is_online is False


@pytest.mark.django_db
def test_is_online_true_with_connections():
    user = User.objects.create_user(
        email="p2@example.com", full_name="P2", password="s3cret-pass-123",
        presence_connections=2,
    )
    assert user.is_online is True
    assert UserSerializer(user).data["is_online"] is True
