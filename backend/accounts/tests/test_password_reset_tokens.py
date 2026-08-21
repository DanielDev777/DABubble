from urllib.parse import parse_qs, urlparse

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.tokens import (
    check_reset_token,
    get_user_from_uid,
    make_reset_link,
    make_uid,
)

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="ada@example.com", full_name="Ada Lovelace", password="s3cret-pass-123"
    )


def _params(link):
    return parse_qs(urlparse(link).query)


@pytest.mark.django_db
def test_reset_link_points_at_the_frontend(user):
    link = make_reset_link(user)
    assert link.startswith(f"{settings.FRONTEND_URL}/reset-password?")


@pytest.mark.django_db
def test_reset_link_carries_uid_and_token(user):
    params = _params(make_reset_link(user))
    assert params["uid"][0]
    assert params["token"][0]


@pytest.mark.django_db
def test_uid_round_trips_to_the_same_user(user):
    assert get_user_from_uid(make_uid(user)) == user


@pytest.mark.django_db
def test_malformed_uid_returns_none(user):
    for bad in ("", "!!!", "not-base64", "MTIzNDU2Nzg5"):
        assert get_user_from_uid(bad) is None


@pytest.mark.django_db
def test_token_verifies_for_its_own_user(user):
    params = _params(make_reset_link(user))
    assert check_reset_token(user, params["token"][0]) is True


@pytest.mark.django_db
def test_token_does_not_verify_for_another_user(user):
    other = User.objects.create_user(
        email="grace@example.com", full_name="Grace Hopper", password="s3cret-pass-123"
    )
    params = _params(make_reset_link(user))
    assert check_reset_token(other, params["token"][0]) is False


@pytest.mark.django_db
def test_token_dies_when_the_password_changes(user):
    token = _params(make_reset_link(user))["token"][0]
    user.set_password("a-different-pass-123")
    user.save()
    assert check_reset_token(user, token) is False


@pytest.mark.django_db
def test_expired_token_is_rejected(user, settings):
    token = _params(make_reset_link(user))["token"][0]
    settings.PASSWORD_RESET_TIMEOUT = -1
    assert check_reset_token(user, token) is False
