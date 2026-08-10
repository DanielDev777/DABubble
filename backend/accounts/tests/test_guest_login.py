import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import DEFAULT_AVATAR_SLUGS

User = get_user_model()


@pytest.mark.django_db
def test_guest_login_creates_throwaway_user():
    client = APIClient()
    response = client.post("/api/auth/guest/", format="json")
    assert response.status_code == 201
    assert response.data["user"]["is_guest"] is True
    assert response.data["user"]["full_name"] == "Guest"
    assert response.data["user"]["default_avatar"] in DEFAULT_AVATAR_SLUGS
    assert settings.AUTH_COOKIE_ACCESS in response.cookies
    assert "csrftoken" in response.cookies

    user = User.objects.get(id=response.data["user"]["id"])
    assert user.is_guest is True
    assert not user.has_usable_password()
    assert user.privacy_accepted_at is None


@pytest.mark.django_db
def test_each_guest_login_is_a_distinct_user():
    client = APIClient()
    first = client.post("/api/auth/guest/", format="json")
    second = APIClient().post("/api/auth/guest/", format="json")
    assert first.data["user"]["id"] != second.data["user"]["id"]
    assert first.data["user"]["email"] != second.data["user"]["email"]
    assert User.objects.filter(is_guest=True).count() == 2


@pytest.mark.django_db
def test_guest_cookies_authenticate_me():
    client = APIClient()
    client.post("/api/auth/guest/", format="json")
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.data["is_guest"] is True


@pytest.mark.django_db
def test_guest_auto_joins_demo_channels():
    from chat.models import Channel, ChannelMembership

    owner = User.objects.create_user(
        email="owner@example.com", full_name="Owner", password="s3cret-pass-123"
    )
    demo = Channel.objects.create(name="General", owner=owner, is_demo=True)
    Channel.objects.create(name="NotDemo", owner=owner, is_demo=False)

    client = APIClient()
    response = client.post("/api/auth/guest/", format="json")
    guest_id = response.data["user"]["id"]

    assert ChannelMembership.objects.filter(channel=demo, user_id=guest_id).exists()
    names = {c["name"] for c in client.get("/api/channels/").data}
    assert "General" in names
    assert "NotDemo" not in names


@pytest.mark.django_db
def test_real_signup_does_not_join_demo_channels():
    from chat.models import Channel, ChannelMembership

    owner = User.objects.create_user(
        email="owner@example.com", full_name="Owner", password="s3cret-pass-123"
    )
    demo = Channel.objects.create(name="General", owner=owner, is_demo=True)

    client = APIClient()
    client.post(
        "/api/auth/signup/",
        {
            "first_name": "Real", "last_name": "User",
            "email": "real@example.com", "password": "s3cret-pass-123",
            "consent": True,
        },
        format="json",
    )
    real = User.objects.get(email="real@example.com")
    assert not ChannelMembership.objects.filter(channel=demo, user=real).exists()
