import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


@pytest.mark.django_db
def test_reset_presence_zeroes_all_counts():
    User.objects.create_user(
        email="a@example.com", full_name="A", password="s3cret-pass-123",
        presence_connections=3,
    )
    User.objects.create_user(
        email="b@example.com", full_name="B", password="s3cret-pass-123",
        presence_connections=1,
    )
    call_command("reset_presence")
    assert list(User.objects.values_list("presence_connections", flat=True)) == [0, 0]
