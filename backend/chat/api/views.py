from django.db.models import Count, Max
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404 as drf_get_object_or_404
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.serializers import UserSerializer
from accounts.models import User
from chat.api.pagination import MessageCursorPagination, ThreadCursorPagination
from chat.api.permissions import IsChannelOwner
from chat.api.serializers import ChannelSerializer, MessageSerializer
from chat.broadcast import broadcast_to_channel
from chat.mentions import sync_mentions
from chat.models import Attachment, Channel, ChannelMembership, Message, Reaction
from chat.reactions import ALLOWED_REACTIONS
from chat.uploads import MAX_ATTACHMENTS_PER_MESSAGE, validate_attachment

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
            .exclude(is_dm=True)
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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return (
            Message.objects.filter(channel__members=self.request.user)
            .select_related("author", "channel")
            .prefetch_related("reactions__user")
        )

    def _member_channel_or_404(self, channel_id):
        if channel_id in (None, ""):
            raise Http404("channel is required.")
        return drf_get_object_or_404(
            Channel, pk=channel_id, members=self.request.user
        )

    def _member_message_or_404(self, message_id):
        if message_id in (None, ""):
            raise Http404("message not found.")
        return drf_get_object_or_404(self.get_queryset(), pk=message_id)

    def list(self, request, *args, **kwargs):
        parent_id = request.query_params.get("parent")
        if parent_id:
            parent = self._member_message_or_404(parent_id)
            qs = self.get_queryset().filter(parent_id=parent.id).order_by("created_at")
            paginator = ThreadCursorPagination()
            page = paginator.paginate_queryset(qs, request, view=self)
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        channel_id = request.query_params.get("channel")
        self._member_channel_or_404(channel_id)
        qs = (
            self.get_queryset()
            .filter(channel_id=channel_id, parent__isnull=True)
            .annotate(
                _reply_count=Count("replies"),
                _last_reply_at=Max("replies__created_at"),
            )
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        parent_id = request.data.get("parent")
        if parent_id:
            parent = self._member_message_or_404(parent_id)
            if parent.parent_id is not None:
                return Response(
                    {"detail": "You can only reply to a top-level message."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            channel = parent.channel
        else:
            parent = None
            channel = self._member_channel_or_404(request.data.get("channel"))
        files = request.FILES.getlist("files")
        content = request.data.get("content", "") or ""

        if len(files) > MAX_ATTACHMENTS_PER_MESSAGE:
            return Response(
                {"detail": f"At most {MAX_ATTACHMENTS_PER_MESSAGE} files per message."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for f in files:
            validate_attachment(f)
        if not content.strip() and not files:
            return Response(
                {"detail": "A message needs text or at least one file."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(author=request.user, channel=channel, parent=parent)
        for f in files:
            Attachment.objects.create(
                message=message,
                file=f,
                original_name=f.name,
                content_type=f.content_type,
                size=f.size,
            )
        sync_mentions(message)

        data = self.get_serializer(message).data
        broadcast_to_channel(channel.id, {"type": "message_created", "message": data})
        return Response(data, status=status.HTTP_201_CREATED)

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
        is_author = message.author_id == request.user.id
        is_owner = channel.owner_id == request.user.id
        if not (is_author or is_owner):
            return Response(
                {"detail": "You cannot delete this message."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Author deleting a message with no replies -> hard delete. Otherwise
        # (author-with-replies, or owner moderating) -> soft delete to keep the
        # thread intact.
        if is_author and not message.replies.exists():
            mid = message.id
            parent_id = message.parent_id
            message.delete()
            broadcast_to_channel(
                channel.id,
                {
                    "type": "message_deleted",
                    "id": mid,
                    "channel": channel.id,
                    "parent": parent_id,
                },
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        message.is_deleted = True
        message.content = ""
        message.save(update_fields=["is_deleted", "content"])
        broadcast_to_channel(
            channel.id,
            {"type": "message_updated", "message": self.get_serializer(message).data},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def react(self, request, pk=None):
        message = self._member_message_or_404(pk)
        emoji = request.data.get("emoji")
        if emoji not in ALLOWED_REACTIONS:
            return Response(
                {"detail": "Unsupported reaction."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if message.is_deleted:
            return Response(
                {"detail": "Cannot react to a deleted message."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        existing = Reaction.objects.filter(
            message=message, user=request.user, emoji=emoji
        ).first()
        if existing:
            existing.delete()
        else:
            Reaction.objects.create(message=message, user=request.user, emoji=emoji)

        fresh = self.get_queryset().get(pk=message.pk)
        data = self.get_serializer(fresh).data
        broadcast_to_channel(
            message.channel_id, {"type": "message_updated", "message": data}
        )
        return Response(data)
