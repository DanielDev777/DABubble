from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.serializers import UserSerializer
from accounts.models import User
from chat.api.pagination import MessageCursorPagination
from chat.api.permissions import IsChannelOwner
from chat.api.serializers import ChannelSerializer, MessageSerializer
from chat.broadcast import broadcast_to_channel
from chat.models import Channel, ChannelMembership, Message

OWNER_ACTIONS = {"update", "partial_update", "destroy", "add_member", "kick", "transfer"}


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer

    def get_permissions(self):
        if self.action in OWNER_ACTIONS:
            return [IsAuthenticated(), IsChannelOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return (
            Channel.objects.filter(members=self.request.user)
            .distinct()
            .order_by("name")
        )

    def perform_create(self, serializer):
        channel = serializer.save(owner=self.request.user)
        ChannelMembership.objects.create(channel=channel, user=self.request.user)

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

    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        channel = self.get_object()
        target = get_object_or_404(User, pk=request.data.get("user_id"))
        _, created = ChannelMembership.objects.get_or_create(
            channel=channel, user=target
        )
        if not created:
            return Response(
                {"detail": "Already a member."}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(self.get_serializer(channel).data)

    @action(detail=True, methods=["post"])
    def kick(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get("user_id")
        if str(user_id) == str(request.user.id):
            return Response(
                {"detail": "You cannot kick yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        membership = ChannelMembership.objects.filter(
            channel=channel, user_id=user_id
        ).first()
        if membership is None:
            return Response(
                {"detail": "That user is not a member."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        channel = self.get_object()
        user_id = request.data.get("user_id")
        if not ChannelMembership.objects.filter(
            channel=channel, user_id=user_id
        ).exists():
            return Response(
                {"detail": "New owner must be a current member."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        channel.owner_id = user_id
        channel.save(update_fields=["owner", "updated_at"])
        return Response(self.get_serializer(channel).data)

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        channel = self.get_object()
        cards = UserSerializer(
            channel.members.all(), many=True, context={"request": request}
        )
        return Response(cards.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    pagination_class = MessageCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            channel__members=self.request.user
        ).select_related("author", "channel")

    def _member_channel_or_404(self, channel_id):
        if channel_id in (None, ""):
            raise Http404("channel is required.")
        return drf_get_object_or_404(
            Channel, pk=channel_id, members=self.request.user
        )

    def list(self, request, *args, **kwargs):
        channel_id = request.query_params.get("channel")
        self._member_channel_or_404(channel_id)
        qs = self.filter_queryset(self.get_queryset().filter(channel_id=channel_id))
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        channel = self._member_channel_or_404(request.data.get("channel"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        broadcast_to_channel(
            channel.id, {"type": "message_created", "message": serializer.data}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        message = self.get_object()
        if message.author_id != request.user.id:
            return Response(
                {"detail": "Only the author can edit this message."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if message.is_deleted:
            return Response(
                {"detail": "Cannot edit a deleted message."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(message, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(edited_at=timezone.now())
        broadcast_to_channel(
            message.channel_id, {"type": "message_updated", "message": serializer.data}
        )
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        channel = message.channel
        if message.author_id == request.user.id:
            mid = message.id
            message.delete()
            broadcast_to_channel(
                channel.id,
                {"type": "message_deleted", "id": mid, "channel": channel.id},
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        if channel.owner_id == request.user.id:
            message.is_deleted = True
            message.content = ""
            message.save(update_fields=["is_deleted", "content"])
            broadcast_to_channel(
                channel.id,
                {
                    "type": "message_updated",
                    "message": self.get_serializer(message).data,
                },
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "You cannot delete this message."},
            status=status.HTTP_403_FORBIDDEN,
        )
