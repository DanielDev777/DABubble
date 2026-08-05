from rest_framework.routers import DefaultRouter

from chat.api.views import ChannelViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"channels", ChannelViewSet, basename="channel")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = router.urls
