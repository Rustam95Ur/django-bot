from rest_framework import routers

from common_users.api.viewset import CommonUserViewSet

router = routers.SimpleRouter()
router.register("", CommonUserViewSet)

urlpatterns = router.urls
