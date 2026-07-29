from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from accounts.managers import UserManager

DEFAULT_AVATAR_SLUGS = ["bald-beard", "quiff", "long-hair", "dark-hair", "bob", "wavy-hair"]
DEFAULT_AVATAR_CHOICES = [(slug, slug) for slug in DEFAULT_AVATAR_SLUGS]


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    default_avatar = models.CharField(
        max_length=20, choices=DEFAULT_AVATAR_CHOICES, null=True, blank=True
    )
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    google_sub = models.CharField(max_length=255, unique=True, null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    is_guest = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def __str__(self):
        return self.email
