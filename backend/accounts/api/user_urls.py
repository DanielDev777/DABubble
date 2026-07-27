from django.urls import path

from accounts.api.views import UserDetailView

urlpatterns = [
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
