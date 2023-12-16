from django.contrib.auth.base_user import BaseUserManager
from common_users.constants import UserType


class UserManager(BaseUserManager):
    """UserManager"""

    use_in_migrations = True

    def create(self, **kwargs):
        instance = super().create(**kwargs)
        instance.set_password(instance.password)
        instance.save()
        return instance

    def create_superuser(self, **kwargs):
        instance = self.create(**kwargs)
        instance.is_superuser = True
        instance.is_staff = True
        instance.user_type = UserType.ADMIN
        instance.save()
        return instance
