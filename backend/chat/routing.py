from django.urls import path

from chat.consumers import ChannelConsumer

websocket_urlpatterns = [
    path("ws/channel/<int:channel_id>/", ChannelConsumer.as_asgi()),
]
