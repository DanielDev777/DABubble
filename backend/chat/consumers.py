import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import ChannelMembership


@database_sync_to_async
def _is_member(user_id, channel_id):
    return ChannelMembership.objects.filter(
        channel_id=channel_id, user_id=user_id
    ).exists()


class ChannelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        self.channel_id = self.scope["url_route"]["kwargs"]["channel_id"]
        if user is None or user.is_anonymous or not await _is_member(
            user.id, self.channel_id
        ):
            await self.close()
            return
        self.group = f"channel_{self.channel_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def message_created(self, event):
        await self.send(text_data=json.dumps(
            {"type": "message.created", "message": event["message"]}
        ))

    async def message_updated(self, event):
        await self.send(text_data=json.dumps(
            {"type": "message.updated", "message": event["message"]}
        ))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps(
            {
                "type": "message.deleted",
                "id": event["id"],
                "channel": event["channel"],
                "parent": event.get("parent"),
            }
        ))
