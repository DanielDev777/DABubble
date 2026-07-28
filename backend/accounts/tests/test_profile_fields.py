import pytest
from django.contrib.auth import get_user_model

from accounts.models import DEFAULT_AVATAR_SLUGS

User = get_user_model()


def test_default_avatar_slugs_are_the_expected_six():
    assert DEFAULT_AVATAR_SLUGS == [
        "bald-beard", "quiff", "long-hair", "dark-hair", "bob", "wavy-hair",
    ]


@pytest.mark.django_db
def test_new_user_profile_fields_default_to_empty():
    user = User.objects.create_user(
        email="p@example.com", full_name="P", password="s3cret-pass"
    )
    assert not user.avatar
    assert user.default_avatar is None
    assert user.privacy_accepted_at is None
    assert user.google_sub is None
    assert user.avatar_url is None
