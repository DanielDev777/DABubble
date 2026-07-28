from unittest.mock import patch

import pytest

from accounts.google import GoogleTokenError, verify_google_id_token


@patch("accounts.google.id_token.verify_oauth2_token")
def test_verify_returns_claims(mock_verify):
    mock_verify.return_value = {"sub": "123", "email": "a@example.com"}
    claims = verify_google_id_token("some-token")
    assert claims["sub"] == "123"
    mock_verify.assert_called_once()


@patch("accounts.google.id_token.verify_oauth2_token", side_effect=ValueError("bad token"))
def test_verify_raises_on_invalid(mock_verify):
    with pytest.raises(GoogleTokenError):
        verify_google_id_token("bad-token")
