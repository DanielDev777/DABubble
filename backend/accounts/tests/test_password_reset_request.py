import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

URL = "/api/auth/password-reset/"


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="ada@example.com", full_name="Ada Lovelace", password="s3cret-pass-123"
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_known_email_sends_a_reset_link(client, user, mailoutbox):
    response = client.post(URL, {"email": "ada@example.com"}, format="json")
    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["ada@example.com"]


@pytest.mark.django_db
def test_unknown_email_sends_nothing(client, db, mailoutbox):
    response = client.post(URL, {"email": "nobody@example.com"}, format="json")
    assert response.status_code == 200
    assert mailoutbox == []


@pytest.mark.django_db
def test_response_does_not_reveal_whether_the_account_exists(client, user, mailoutbox):
    known = client.post(URL, {"email": "ada@example.com"}, format="json")
    unknown = client.post(URL, {"email": "nobody@example.com"}, format="json")
    assert known.status_code == unknown.status_code == 200
    assert known.data == unknown.data


@pytest.mark.django_db
def test_malformed_email_is_rejected(client, db, mailoutbox):
    response = client.post(URL, {"email": "not-an-email"}, format="json")
    assert response.status_code == 400
    assert "email" in response.data
    assert mailoutbox == []


@pytest.mark.django_db
def test_missing_email_is_rejected(client, db, mailoutbox):
    response = client.post(URL, {}, format="json")
    assert response.status_code == 400
    assert mailoutbox == []


@pytest.mark.django_db
def test_email_lookup_is_case_insensitive(client, user, mailoutbox):
    response = client.post(URL, {"email": "ADA@Example.COM"}, format="json")
    assert response.status_code == 200
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_guest_accounts_get_no_reset_mail(client, db, mailoutbox):
    guest = User.objects.create_user(
        email="guest_abc123@guest.local", full_name="Guest", password=None, is_guest=True
    )
    response = client.post(URL, {"email": guest.email}, format="json")
    assert response.status_code == 200
    assert mailoutbox == []


@pytest.mark.django_db
def test_google_only_account_can_reset(client, db, mailoutbox):
    # No usable password, but they control the mailbox, so let them set one.
    google_user = User.objects.create_user(
        email="grace@example.com",
        full_name="Grace Hopper",
        password=None,
        google_sub="google-sub-1",
    )
    response = client.post(URL, {"email": google_user.email}, format="json")
    assert response.status_code == 200
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_inactive_account_gets_no_reset_mail(client, user, mailoutbox):
    user.is_active = False
    user.save(update_fields=["is_active"])
    response = client.post(URL, {"email": user.email}, format="json")
    assert response.status_code == 200
    assert mailoutbox == []


@pytest.mark.django_db
def test_requests_are_rate_limited(client, user, mailoutbox):
    for _ in range(5):
        assert client.post(URL, {"email": user.email}, format="json").status_code == 200
    blocked = client.post(URL, {"email": user.email}, format="json")
    assert blocked.status_code == 429
    assert len(mailoutbox) == 5
