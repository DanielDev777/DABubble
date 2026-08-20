from django.db.models import Count
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from chat.api.pagination import NotificationCursorPagination
from chat.api.serializers import NotificationSerializer
from chat.models import Notification


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    pagination_class = NotificationCursorPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user).select_related(
            "message__author", "message__channel"
        )
        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(is_read=False)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        rows = (
            Notification.objects.filter(user=request.user, is_read=False)
            .values("message__channel")
            .annotate(count=Count("id"))
        )
        return Response(
            {
                "unread_total": sum(row["count"] for row in rows),
                "by_channel": {
                    str(row["message__channel"]): row["count"] for row in rows
                },
            }
        )

    @action(detail=False, methods=["post"])
    def read(self, request):
        ids = request.data.get("ids")
        mark_all = request.data.get("all")
        channel_id = request.data.get("channel")
        given = [
            value
            for value in (ids, mark_all, channel_id)
            if value not in (None, False)
        ]
        if len(given) != 1:
            return Response(
                {"detail": 'Send exactly one of "ids", "all", or "channel".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = Notification.objects.filter(user=request.user, is_read=False)
        if ids is not None:
            qs = qs.filter(id__in=ids)
        elif channel_id is not None:
            qs = qs.filter(message__channel_id=channel_id)
        marked = qs.update(is_read=True)
        unread_total = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({"marked": marked, "unread_total": unread_total})
