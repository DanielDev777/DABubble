from django.urls import path

from accounts.consumers import PresenceConsumer

websocket_urlpatterns = [
    path("ws/presence/", PresenceConsumer.as_asgi()),
]
