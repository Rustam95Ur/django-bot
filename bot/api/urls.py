from rest_framework import routers

from bot.api.viewset import UseChatHistoryViewSet, UserViewSet

router = routers.SimpleRouter()
router.register("user", UserViewSet)
router.register("chat", UseChatHistoryViewSet)

urlpatterns = router.urls
