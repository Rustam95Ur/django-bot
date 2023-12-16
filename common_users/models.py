from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from phonenumber_field.modelfields import PhoneNumberField

from common_users.managers import UserManager
from core.models.base import BaseUUIDModel

from common_users.constants import (
    UserType,
)


class CommonUser(AbstractBaseUser, PermissionsMixin, BaseUUIDModel):
    """CommonUser"""

    phone = PhoneNumberField(verbose_name=_("Phone"))
    username = models.CharField(verbose_name=_("Username"))
    user_type = models.PositiveSmallIntegerField(
        verbose_name=_("User type"),
        choices=UserType.CHOICES,
        default=UserType.CLIENT,
    )
    email = models.EmailField(
        verbose_name=_("Email address"), blank=True, null=True
    )
    first_name = models.CharField(
        verbose_name=_("First name"), max_length=32, blank=True, default=""
    )
    last_name = models.CharField(
        verbose_name=_("Last name"), max_length=255, blank=True, null=True
    )
    birthday = models.DateField(
        verbose_name=_("Date of birthday"), null=True, blank=True
    )
    is_active = models.BooleanField(verbose_name=_("Is active"), default=True)
    is_staff = models.BooleanField(verbose_name=_("Is staff"), default=False)
    chat_id = models.CharField(
        verbose_name=_("Chat id"), max_length=100, null=True, blank=True
    )
    telegram_user_id = models.CharField(
        verbose_name=_("Telegram user id"), max_length=100, unique=True
    )
    USERNAME_FIELD = "telegram_user_id"
    USERTYPE_FIELD = "user_type"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = _("CommonUser")
        verbose_name_plural = _("CommonUsers")
        db_table = "common_users"
        unique_together = ["phone", "user_type"]

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"


class FAQ(BaseUUIDModel):
    """FAQ"""

    question = models.TextField(verbose_name=_("Question"))
    answer = models.TextField(verbose_name=_("Answer"))

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        db_table = "faqs"

    def __str__(self):
        return f"{self.question}"
