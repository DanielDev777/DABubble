from django.contrib.auth import get_user_model
from django.db.models import F, Max
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.api.serializers import DmSerializer
from chat.models import Channel, ChannelMembership

User = get_user_model()


def dm_name(a_id, b_id):
    low, high = sorted((a_id, b_id))
    return f"dm:{low}:{high}"


class DmView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dms = (
            Channel.objects.filter(is_dm=True, members=request.user)
            .prefetch_related("members")
            .annotate(last_activity=Max("messages__created_at"))
            .order_by(F("last_activity").desc(nulls_last=True), "-created_at")
        )
        return Response(
            DmSerializer(dms, many=True, context={"request": request}).data
        )

    def post(self, request):
        target = get_object_or_404(User, pk=request.data.get("user_id"))
        channel, created = Channel.objects.get_or_create(
            name=dm_name(request.user.id, target.id),
            defaults={"owner": request.user, "is_dm": True, "description": ""},
        )
        ChannelMembership.objects.get_or_create(channel=channel, user=request.user)
        if target.id != request.user.id:
            ChannelMembership.objects.get_or_create(channel=channel, user=target)
        data = DmSerializer(channel, context={"request": request}).data
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(data, status=code)
