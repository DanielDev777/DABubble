import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_email_and_password():
    user = User.objects.create_user(
        email="alice@example.com", full_name="Alice", password="s3cret-pass"
    )
    assert user.email == "alice@example.com"
    assert user.full_name == "Alice"
    assert user.check_password("s3cret-pass")
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_email_is_normalized():
    user = User.objects.create_user(
        email="Bob@EXAMPLE.com", full_name="Bob", password="s3cret-pass"
    )
    assert user.email == "Bob@example.com"


@pytest.mark.django_db
def test_email_is_required():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", full_name="NoEmail", password="x")


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(
        email="admin@example.com", full_name="Admin", password="s3cret-pass"
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_username_field_is_email():
    assert User.USERNAME_FIELD == "email"
    assert "email" not in User.REQUIRED_FIELDS
    assert User.REQUIRED_FIELDS == ["full_name"]
