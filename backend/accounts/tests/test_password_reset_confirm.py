from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.tokens import make_reset_link, make_uid

User = get_user_model()

URL = "/api/auth/password-reset/confirm/"
OLD_PASSWORD = "s3cret-pass-123"
NEW_PASSWORD = "brand-new-pass-456"


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="ada@example.com", full_name="Ada Lovelace", password=OLD_PASSWORD
    )


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def link(user):
    params = parse_qs(urlparse(make_reset_link(user)).query)
    return {"uid": params["uid"][0], "token": params["token"][0]}


def _payload(link, password=NEW_PASSWORD):
    return {**link, "password": password}


@pytest.mark.django_db
def test_valid_link_sets_the_new_password(client, user, link):
    response = client.post(URL, _payload(link), format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert not user.check_password(OLD_PASSWORD)


@pytest.mark.django_db
def test_user_can_log_in_with_the_new_password(client, user, link):
    client.post(URL, _payload(link), format="json")
    response = client.post(
        "/api/auth/login/",
        {"email": user.email, "password": NEW_PASSWORD},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_old_password_stops_working(client, user, link):
    client.post(URL, _payload(link), format="json")
    response = client.post(
        "/api/auth/login/",
        {"email": user.email, "password": OLD_PASSWORD},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_tampered_token_is_rejected(client, user, link):
    response = client.post(
        URL, _payload({**link, "token": link["token"] + "x"}), format="json"
    )
    assert response.status_code == 400
    assert "detail" in response.data
    user.refresh_from_db()
    assert user.check_password(OLD_PASSWORD)


@pytest.mark.django_db
def test_garbage_uid_is_rejected(client, user, link):
    response = client.post(URL, _payload({**link, "uid": "!!!"}), format="json")
    assert response.status_code == 400
    assert "detail" in response.data


@pytest.mark.django_db
def test_uid_of_a_deleted_user_is_rejected(client, user, link):
    other = User.objects.create_user(
        email="grace@example.com", full_name="Grace Hopper", password=OLD_PASSWORD
    )
    stale_uid = make_uid(other)
    other.delete()
    response = client.post(URL, _payload({**link, "uid": stale_uid}), format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_weak_password_is_rejected_with_field_errors(client, user, link):
    response = client.post(URL, _payload(link, password="123"), format="json")
    assert response.status_code == 400
    assert "password" in response.data
    user.refresh_from_db()
    assert user.check_password(OLD_PASSWORD)


@pytest.mark.django_db
def test_a_weak_attempt_does_not_burn_the_link(client, user, link):
    assert client.post(URL, _payload(link, password="123"), format="json").status_code == 400
    response = client.post(URL, _payload(link), format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


@pytest.mark.django_db
def test_link_is_single_use(client, user, link):
    assert client.post(URL, _payload(link), format="json").status_code == 200
    replay = client.post(URL, _payload(link, password="another-pass-789"), format="json")
    assert replay.status_code == 400
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


@pytest.mark.django_db
def test_expired_link_is_rejected(client, user, link, settings):
    settings.PASSWORD_RESET_TIMEOUT = -1
    response = client.post(URL, _payload(link), format="json")
    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password(OLD_PASSWORD)


@pytest.mark.django_db
def test_missing_fields_are_rejected(client, user):
    response = client.post(URL, {"password": NEW_PASSWORD}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_reset_revokes_existing_sessions(client, user, link):
    session = APIClient()
    session.post(
        "/api/auth/login/",
        {"email": user.email, "password": OLD_PASSWORD},
        format="json",
    )
    assert session.post("/api/auth/refresh/").status_code == 200

    client.post(URL, _payload(link), format="json")

    assert session.post("/api/auth/refresh/").status_code == 401
