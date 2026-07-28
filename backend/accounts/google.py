from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


class GoogleTokenError(Exception):
    """Raised when a Google ID token fails verification."""


def verify_google_id_token(token):
    """Verify a Google ID token and return its claims.

    Checks signature, audience (our client id), issuer, and expiry via
    google-auth. Raises GoogleTokenError on any failure.
    """
    try:
        return id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_AUTH_CLIENT_ID
        )
    except ValueError as exc:
        raise GoogleTokenError(str(exc)) from exc
