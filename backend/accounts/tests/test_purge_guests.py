from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
def test_purge_guests_deletes_only_old_guests():
    now = timezone.now()

    old_guest = User.objects.create_user(
        email="old@guest.local", full_name="Guest", is_guest=True
    )
    User.objects.filter(pk=old_guest.pk).update(date_joined=now - timedelta(days=10))

    recent_guest = User.objects.create_user(
        email="new@guest.local", full_name="Guest", is_guest=True
    )

    real_user = User.objects.create_user(
        email="real@example.com", full_name="Real", password="s3cret-pass-123"
    )
    User.objects.filter(pk=real_user.pk).update(date_joined=now - timedelta(days=100))

    call_command("purge_guests", "--days", "7")

    assert not User.objects.filter(pk=old_guest.pk).exists()
    assert User.objects.filter(pk=recent_guest.pk).exists()
    assert User.objects.filter(pk=real_user.pk).exists()
