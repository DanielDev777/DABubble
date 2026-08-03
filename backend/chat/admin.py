from django.contrib import admin

from chat.models import Channel, ChannelMembership


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_private", "created_at")
    search_fields = ("name",)


@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "joined_at")
