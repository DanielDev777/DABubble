from django.urls import path

from accounts.api.views import (
    GoogleLoginView,
    GuestLoginView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    SignupView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("guest/", GuestLoginView.as_view(), name="guest-login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
