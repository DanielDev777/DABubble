import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


def _emails(results):
    return {u["email"] for u in results}


@pytest.mark.django_db
def test_search_users_by_name_partial(make_user, client_for):
    me = make_user("me@example.com")
    make_user("alice@example.com")  # full_name defaults to "alice"
    make_user("bob@example.com")
    data = client_for(me).get("/api/search/?q=ali").data
    assert "alice@example.com" in _emails(data["users"])
    assert "bob@example.com" not in _emails(data["users"])


@pytest.mark.django_db
def test_search_users_by_email_partial(make_user, client_for):
    me = make_user("me@example.com")
    User.objects.create_user(
        email="zoe@corp.com", full_name="Zoe", password="s3cret-pass-123"
    )
    data = client_for(me).get("/api/search/?q=corp").data
    assert "zoe@corp.com" in _emails(data["users"])


@pytest.mark.django_db
def test_search_excludes_self_and_guests(make_user, client_for):
    me = make_user("findme@example.com")
    User.objects.create_user(
        email="guest_x@guest.local", full_name="findme guest",
        password="s3cret-pass-123", is_guest=True,
    )
    data = client_for(me).get("/api/search/?q=findme").data
    emails = _emails(data["users"])
    assert "findme@example.com" not in emails  # self excluded
    assert "guest_x@guest.local" not in emails  # guest excluded


@pytest.mark.django_db
def test_search_response_has_all_three_keys(make_user, client_for):
    me = make_user("me@example.com")
    data = client_for(me).get("/api/search/?q=x").data
    assert set(data.keys()) == {"users", "channels", "messages"}
