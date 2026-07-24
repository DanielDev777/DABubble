from django.urls import path

from accounts.api.views import LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
]
