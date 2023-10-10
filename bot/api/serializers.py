from django.contrib.auth.models import User
from rest_framework import serializers

from bot.models import UseChatHistory


class UseChatHistorySerializer(serializers.ModelSerializer):
    """UseChatHistorySerializer"""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault)

    class Meta:
        model = UseChatHistory
        fields = [
            "user",
            "message"
        ]


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        password = attrs['password']
        password2 = attrs.pop('password2')

        if password != password2:
            raise serializers.ValidationError(
                {'password': 'Passwords must match.'}
            )

        return attrs

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(validated_data.get("password"))
        user.save()
        return user
