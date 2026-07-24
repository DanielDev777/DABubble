from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("api/auth/", include("accounts.api.urls")),  # enabled in Task 4
]
