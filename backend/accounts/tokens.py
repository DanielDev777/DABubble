"""Signed, single-use password-reset links.

The token is Django's own: it derives from the user's primary key, password hash,
``last_login`` and a timestamp, so changing the password (or logging in) makes any
outstanding token stop verifying. That is what makes a reset link single-use
without storing anything in the database.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


def make_uid(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def get_user_from_uid(uidb64):
    """Return the user a base64 uid points at, or None if it is unusable."""
    try:
        pk = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def check_reset_token(user, token):
    return default_token_generator.check_token(user, token)


def make_reset_link(user):
    """Build the reset URL the user clicks in their email.

    The host comes from settings, never from the incoming request: trusting
    ``request.get_host()`` here would let a spoofed Host header rewrite reset
    links to point at an attacker's domain.
    """
    uid = make_uid(user)
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"


def revoke_refresh_tokens(user):
    """Blacklist every outstanding refresh token for a user.

    Called after a password reset: the plausible reason for resetting is that
    somebody else has access, so existing sessions should not survive it.
    """
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def record_outstanding_token(refresh):
    """Register a rotated refresh token in the blacklist app's ledger.

    ``RefreshToken.for_user()`` writes this row itself, but a token rotated in
    place with ``set_jti()`` never passes through it. Without this, rotated
    tokens are invisible to bulk revocation.
    """
    from rest_framework_simplejwt.settings import api_settings
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    from rest_framework_simplejwt.utils import datetime_from_epoch

    OutstandingToken.objects.get_or_create(
        jti=refresh[api_settings.JTI_CLAIM],
        defaults={
            "user_id": refresh.get(api_settings.USER_ID_CLAIM),
            "token": str(refresh),
            "created_at": refresh.current_time,
            "expires_at": datetime_from_epoch(refresh["exp"]),
        },
    )
