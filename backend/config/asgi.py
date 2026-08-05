import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from accounts.routing import websocket_urlpatterns as presence_ws  # noqa: E402
from accounts.ws_auth import JWTCookieAuthMiddleware  # noqa: E402
from chat.routing import websocket_urlpatterns as chat_ws  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTCookieAuthMiddleware(URLRouter(presence_ws + chat_ws)),
    }
)
