from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "is_staff", "is_active", "is_guest")
    search_fields = ("email", "full_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "avatar", "avatar_url", "default_avatar", "google_sub")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_guest", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "privacy_accepted_at", "presence_connections")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "password1", "password2")}),
    )
