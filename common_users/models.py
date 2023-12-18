from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from phonenumber_field.modelfields import PhoneNumberField

from common_users.managers import UserManager
from core.models.base import BaseUUIDModel

from common_users.constants import (
    UserType,
)
from core.models.model_fields import AmountField


class CommonUser(AbstractBaseUser, PermissionsMixin, BaseUUIDModel):
    """CommonUser"""

    phone = PhoneNumberField(verbose_name=_("Phone"), null=True, blank=True)
    username = models.CharField(verbose_name=_("Username"), unique=True)
    user_type = models.PositiveSmallIntegerField(
        verbose_name=_("User type"),
        choices=UserType.CHOICES,
        default=UserType.CLIENT,
    )
    first_name = models.CharField(
        verbose_name=_("First name"), max_length=32, blank=True, default=""
    )
    last_name = models.CharField(
        verbose_name=_("Last name"), max_length=255, blank=True, null=True
    )
    car_number = models.CharField(
        verbose_name=_("Car number"), max_length=3, blank=True, null=True
    )
    car_serial_number = models.CharField(
        verbose_name=_("Car serial number"),
        max_length=3,
        blank=True,
        null=True,
    )
    car_number_region = models.IntegerField(
        verbose_name=_("Car number region"), null=True, blank=True
    )
    is_active = models.BooleanField(verbose_name=_("Is active"), default=True)
    is_staff = models.BooleanField(verbose_name=_("Is staff"), default=False)
    chat_id = models.CharField(
        verbose_name=_("Chat id"), max_length=100, null=True, blank=True
    )
    telegram_user_id = models.CharField(
        verbose_name=_("Telegram user id"), max_length=100, unique=True
    )

    USERNAME_FIELD = "username"
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


class CommonUserPurchase(BaseUUIDModel):
    """CommonUserPurchase"""

    user = models.ForeignKey(
        "common_users.CommonUser",
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="purchases",
    )
    product = models.ForeignKey(
        "orders.Product",
        on_delete=models.CASCADE,
        verbose_name=_("Product"),
        related_name="purchases",
    )
    quantity = models.IntegerField(verbose_name=_("Quantity"))
    amount = AmountField(verbose_name=_("Amount"))
    is_completed = models.BooleanField(
        verbose_name=_("Is completed"), default=False
    )

    class Meta:
        verbose_name = "CommonUser purchase"
        verbose_name_plural = "CommonUser purchases"
        db_table = "common_user_purchases"
