from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.serializers import UserSerializer
from accounts.models import User
from chat.api.serializers import ChannelSerializer, MessageSerializer
from chat.models import Channel, Message

SEARCH_LIMIT = 20


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        ctx = {"request": request}
        users, channels, messages = [], [], []
        if q:
            users = self._users(request, q)
            channels = self._channels(request, q)
            messages = self._messages(request, q)
        return Response(
            {
                "users": UserSerializer(users, many=True, context=ctx).data,
                "channels": ChannelSerializer(channels, many=True, context=ctx).data,
                "messages": MessageSerializer(messages, many=True, context=ctx).data,
            }
        )

    def _users(self, request, q):
        return (
            User.objects.filter(Q(full_name__icontains=q) | Q(email__icontains=q))
            .exclude(is_guest=True)
            .exclude(id=request.user.id)
            .order_by("full_name")[:SEARCH_LIMIT]
        )

    def _channels(self, request, q):
        return (
            Channel.objects.filter(members=request.user)
            .filter(Q(name__icontains=q) | Q(description__icontains=q))
            .distinct()
            .order_by("name")[:SEARCH_LIMIT]
        )

    def _messages(self, request, q):
        return []
