import requests
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from bot.models import UseChatHistory


class UseChatHistorySerializer(serializers.ModelSerializer):
    """UseChatHistorySerializer"""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UseChatHistory
        fields = [
            "user",
            "message"
        ]

    def create(self, validated_data):
        instance = super().create(validated_data)

        if instance.user.chat_settings.chat_id:

            telegram_chat_id = instance.user.chat_settings.chat_id
            api_url = "https://api.telegram.org/"
            bot_token = settings.TELEGRAM_BOT_TOKEN

            bot_url = f"{api_url}bot{bot_token}/"
            message_url = f"{bot_url}sendMessage"
            formatted_message = f"{instance.user.first_name}, я получил от тебя сообщение: \n{instance.message}"
            message_data = {
                "chat_id": telegram_chat_id,
                "text": formatted_message,
                "parse_mode": "HTML",
            }
            requests.post(message_url, data=message_data)

        return instance


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = User
        fields = ["username", "first_name",  "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, attrs):
        password = attrs["password"]
        password2 = attrs.pop("password2")

        if password != password2:
            raise serializers.ValidationError(
                {"password": "Passwords must match."}
            )

        return attrs

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data.get("password"))
        user.save()
        return user
