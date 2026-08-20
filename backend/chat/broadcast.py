from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_to_channel(channel_id, event):
    """Send an event dict (must include a "type" key) to a channel's WS group."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(f"channel_{channel_id}", event)


def broadcast_to_user(user_id, event):
    """Send an event dict (must include a "type" key) to one user's WS group."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(f"user_{user_id}", event)
