from django.conf import settings
from django.db import models
from django.db.models.functions import Lower


class Channel(models.Model):
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_channels",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ChannelMembership",
        related_name="channels",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("name"), name="unique_channel_name_ci"),
        ]

    def __str__(self):
        return self.name


class ChannelMembership(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("channel", "user")

    def __str__(self):
        return f"{self.user} in {self.channel}"
