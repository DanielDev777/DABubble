from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from chat.api.permissions import IsChannelOwner
from chat.api.serializers import ChannelSerializer
from chat.models import Channel, ChannelMembership

OWNER_ACTIONS = {"update", "partial_update", "destroy", "add_member", "kick", "transfer"}


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer

    def get_permissions(self):
        if self.action in OWNER_ACTIONS:
            return [IsAuthenticated(), IsChannelOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        return (
            Channel.objects.filter(Q(is_private=False) | Q(members=user))
            .distinct()
            .order_by("name")
        )

    def perform_create(self, serializer):
        is_private = bool(self.request.data.get("is_private", False))
        channel = serializer.save(owner=self.request.user, is_private=is_private)
        ChannelMembership.objects.create(channel=channel, user=self.request.user)
