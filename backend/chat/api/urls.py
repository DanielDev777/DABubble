from rest_framework.routers import DefaultRouter

from chat.api.views import ChannelViewSet

router = DefaultRouter()
router.register(r"channels", ChannelViewSet, basename="channel")

urlpatterns = router.urls
