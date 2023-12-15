from rest_framework import serializers

from common_users.models import CommonUser


class CommonUserSerializer(serializers.ModelSerializer):
    """CommonUserSerializer"""

    class Meta:
        model = CommonUser
        fields = ["first_name", "last_name", "phone"]
