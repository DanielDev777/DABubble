from django.contrib import admin

from chat.models import Attachment, Channel, ChannelMembership, Message, Reaction


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "created_at")
    search_fields = ("name",)


@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "joined_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("channel", "author", "created_at", "is_deleted")
    search_fields = ("content",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "message", "content_type", "size", "created_at")


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("emoji", "user", "message", "created_at")
