from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.base import BaseNameModel


class Category(BaseNameModel):
    """Category"""

    is_active = models.BooleanField(verbose_name=_("Is active"), default=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        db_table = "order_categories"


class Product(BaseNameModel):
    """Product"""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
        related_name="products",
    )
    is_active = models.BooleanField(verbose_name=_("Is active"), default=True)
    is_free = models.BooleanField(verbose_name=_("Is free"), default=True)
    is_took_place = models.BooleanField(
        verbose_name=_("Is took place"), default=False
    )
    lessor = models.ForeignKey(
        "common_users.CommonUser",
        on_delete=models.SET_NULL,
        verbose_name=_("Lessor"),
        related_name="products",
        null=True,
        blank=True,
    )
    expiration_date = models.DateTimeField(null=True, blank=True)

    @property
    def str_expiration_date(self):
        expiration_date = self.expiration_date - timedelta(
            minutes=settings.END_MINUTE
        )
        localized_expiration_date = timezone.localtime(expiration_date)

        formatted_datetime = localized_expiration_date.strftime(
            "%d %B %Y, %H:%M:%S"
        )

        return formatted_datetime

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        db_table = "order_products"
