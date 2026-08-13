from django.urls import path
from rest_framework.routers import DefaultRouter

from chat.api.dm import DmView
from chat.api.search import SearchView
from chat.api.views import ChannelViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"channels", ChannelViewSet, basename="channel")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = router.urls + [
    path("search/", SearchView.as_view(), name="search"),
    path("dm/", DmView.as_view(), name="dm"),
]
