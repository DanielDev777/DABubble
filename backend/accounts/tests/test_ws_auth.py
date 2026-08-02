import pytest
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from accounts.ws_auth import JWTCookieAuthMiddleware

User = get_user_model()


@database_sync_to_async
def make_user(email):
    return User.objects.create_user(
        email=email, full_name="P", password="s3cret-pass-123"
    )


async def _run_middleware(headers):
    captured = {}

    async def inner(scope, receive, send):
        captured["user"] = scope["user"]

    mw = JWTCookieAuthMiddleware(inner)
    await mw({"type": "websocket", "headers": headers}, None, None)
    return captured["user"]


@pytest.mark.django_db(transaction=True)
async def test_valid_cookie_sets_user():
    user = await make_user("a@example.com")
    token = str(AccessToken.for_user(user))
    cookie = f"{settings.AUTH_COOKIE_ACCESS}={token}".encode()
    result = await _run_middleware([(b"cookie", cookie)])
    assert result.id == user.id


@pytest.mark.django_db(transaction=True)
async def test_missing_cookie_is_anonymous():
    result = await _run_middleware([])
    assert isinstance(result, AnonymousUser)


@pytest.mark.django_db(transaction=True)
async def test_invalid_cookie_is_anonymous():
    cookie = f"{settings.AUTH_COOKIE_ACCESS}=not-a-real-token".encode()
    result = await _run_middleware([(b"cookie", cookie)])
    assert isinstance(result, AnonymousUser)
