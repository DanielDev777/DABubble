import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.emails import send_password_reset_email

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="ada@example.com", full_name="Ada Lovelace", password="s3cret-pass-123"
    )


@pytest.mark.django_db
def test_sends_one_mail_to_the_user(user, mailoutbox):
    send_password_reset_email(user)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["ada@example.com"]
    assert mailoutbox[0].from_email == settings.DEFAULT_FROM_EMAIL


@pytest.mark.django_db
def test_subject_is_the_german_copy(user, mailoutbox):
    send_password_reset_email(user)
    assert mailoutbox[0].subject == "DABubble – Passwort zurücksetzen"


@pytest.mark.django_db
def test_body_contains_a_frontend_reset_link(user, mailoutbox):
    send_password_reset_email(user)
    body = mailoutbox[0].body
    assert f"{settings.FRONTEND_URL}/reset-password?" in body
    assert "uid=" in body
    assert "token=" in body


@pytest.mark.django_db
def test_body_greets_the_user_by_name(user, mailoutbox):
    send_password_reset_email(user)
    assert "Ada Lovelace" in mailoutbox[0].body


@pytest.mark.django_db
def test_link_is_not_html_escaped(user, mailoutbox):
    # Django autoescapes every template, .txt included: an escaped "&" would
    # hand the frontend an "amp;token" parameter and break every reset.
    send_password_reset_email(user)
    body = mailoutbox[0].body
    assert "&amp;" not in body
    assert "&token=" in body


@pytest.mark.django_db
def test_emailed_link_survives_a_round_trip(user, mailoutbox):
    from urllib.parse import parse_qs, urlparse

    send_password_reset_email(user)
    link = next(
        word for word in mailoutbox[0].body.split() if word.startswith("http")
    )
    params = parse_qs(urlparse(link).query)
    assert set(params) == {"uid", "token"}
