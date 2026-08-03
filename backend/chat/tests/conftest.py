import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

PASSWORD = "s3cret-pass-123"


@pytest.fixture
def make_user(db):
    def _make(email, **kwargs):
        return User.objects.create_user(
            email=email, full_name=email.split("@")[0], password=PASSWORD, **kwargs
        )
    return _make


@pytest.fixture
def client_for():
    def _client(user):
        client = APIClient()
        client.post(
            "/api/auth/login/",
            {"email": user.email, "password": PASSWORD},
            format="json",
        )
        return client
    return _client
