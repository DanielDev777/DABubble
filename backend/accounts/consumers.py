import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import F

from accounts.models import User

PRESENCE_GROUP = "presence"


@database_sync_to_async
def _increment(user_id):
    User.objects.filter(id=user_id).update(
        presence_connections=F("presence_connections") + 1
    )
    return User.objects.get(id=user_id).presence_connections


@database_sync_to_async
def _decrement(user_id):
    User.objects.filter(id=user_id, presence_connections__gt=0).update(
        presence_connections=F("presence_connections") - 1
    )
    return User.objects.get(id=user_id).presence_connections


@database_sync_to_async
def _online_ids():
    return list(
        User.objects.filter(presence_connections__gt=0).values_list("id", flat=True)
    )


class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close()
            return
        self.user_id = user.id
        await self.channel_layer.group_add(PRESENCE_GROUP, self.channel_name)
        await self.accept()

        count = await _increment(self.user_id)
        await self.send(text_data=json.dumps(
            {"type": "presence.snapshot", "online": await _online_ids()}
        ))
        if count == 1:
            await self.channel_layer.group_send(
                PRESENCE_GROUP,
                {"type": "presence.update", "user_id": self.user_id, "is_online": True},
            )

    async def disconnect(self, code):
        if not hasattr(self, "user_id"):
            return
        count = await _decrement(self.user_id)
        await self.channel_layer.group_discard(PRESENCE_GROUP, self.channel_name)
        if count == 0:
            await self.channel_layer.group_send(
                PRESENCE_GROUP,
                {"type": "presence.update", "user_id": self.user_id, "is_online": False},
            )

    async def presence_update(self, event):
        await self.send(text_data=json.dumps(
            {
                "type": "presence.update",
                "user_id": event["user_id"],
                "is_online": event["is_online"],
            }
        ))
