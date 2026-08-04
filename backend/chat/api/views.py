from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        channel = get_object_or_404(Channel, pk=pk)
        if channel.is_private:
            return Response(
                {"detail": "This channel is private."}, status=status.HTTP_403_FORBIDDEN
            )
        _, created = ChannelMembership.objects.get_or_create(
            channel=channel, user=request.user
        )
        if not created:
            return Response(
                {"detail": "Already a member."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(self.get_serializer(channel).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        channel = self.get_object()
        if channel.owner_id == request.user.id:
            return Response(
                {"detail": "Owner must transfer ownership before leaving."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        membership = ChannelMembership.objects.filter(
            channel=channel, user=request.user
        ).first()
        if membership is None:
            return Response(
                {"detail": "Not a member."}, status=status.HTTP_400_BAD_REQUEST
            )
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
