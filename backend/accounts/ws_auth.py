from http.cookies import SimpleCookie

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(raw_token):
    from accounts.models import User

    try:
        token = AccessToken(raw_token)
    except TokenError:
        return AnonymousUser()
    try:
        return User.objects.get(id=token["user_id"])
    except User.DoesNotExist:
        return AnonymousUser()


class JWTCookieAuthMiddleware:
    """Channels middleware that authenticates via the access_token cookie."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        user = AnonymousUser()
        headers = dict(scope.get("headers", []))
        raw_cookie = headers.get(b"cookie")
        if raw_cookie:
            cookies = SimpleCookie()
            cookies.load(raw_cookie.decode())
            morsel = cookies.get(settings.AUTH_COOKIE_ACCESS)
            if morsel is not None:
                user = await _get_user(morsel.value)
        scope["user"] = user
        return await self.app(scope, receive, send)
