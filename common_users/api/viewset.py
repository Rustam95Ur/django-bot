from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common_users.api.serializers import CommonUserSerializer
from common_users.models import CommonUser
from services.telegram_chat_bot import process_telegram_event


class CommonUserViewSet(
    viewsets.GenericViewSet,
    generics.ListAPIView,
):
    """CommonUserViewSet"""

    queryset = CommonUser.objects.all()
    serializer_class = CommonUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    @swagger_auto_schema(
        method="post",
    )
    @action(methods=["POST"], detail=False, permission_classes=[AllowAny])
    def webhooks(self, request, *args, **kwargs):
        process_telegram_event(request.data)
        return Response(status.HTTP_200_OK)
