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
    is_demo = models.BooleanField(default=False)
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


class Message(models.Model):
    channel = models.ForeignKey(
        Channel, on_delete=models.CASCADE, related_name="messages"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages"
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} in {self.channel}: {self.content[:20]}"


class Attachment(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="attachments/%Y/%m/")
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name


class Reaction(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="reactions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reactions"
    )
    emoji = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user", "emoji")

    def __str__(self):
        return f"{self.user} {self.emoji} on {self.message_id}"
