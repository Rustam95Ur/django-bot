from django.contrib.auth.models import User

from drf_yasg.utils import swagger_auto_schema

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from bot.api.serializers import UseChatHistorySerializer, UserSerializer
from bot.models import UseChatHistory
from bot.services.telegram_chat_bot import process_telegram_event


class UseChatHistoryViewSet(
    viewsets.GenericViewSet,
    generics.ListAPIView,
    generics.CreateAPIView
):
    """UseChatHistoryViewSet"""

    queryset = UseChatHistory.objects.all()
    serializer_class = UseChatHistorySerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        method="post",
    )
    @action(methods=["POST"], detail=False, permission_classes=[AllowAny])
    def webhooks(self, request, *args, **kwargs):
        process_telegram_event(request.data)
        return Response(status.HTTP_200_OK)


class UserViewSet(
    viewsets.GenericViewSet,
    generics.CreateAPIView,
    generics.ListAPIView
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(
        method="post",
    )
    @action(methods=["POST"], detail=False)
    def login(self, request, pk=None, *args, **kwargs):
        jwt_serializer = TokenObtainPairSerializer(
            data=request.data,
        )
        jwt_serializer.is_valid(raise_exception=True)
        data = jwt_serializer.validated_data
        return Response(data, status=status.HTTP_200_OK)