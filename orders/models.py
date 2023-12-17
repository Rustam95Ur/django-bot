from django.db import models
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
    lessor = models.ForeignKey(
        "common_users.CommonUser",
        on_delete=models.SET_NULL,
        verbose_name=_("Lessor"),
        related_name="products",
        null=True,
        blank=True,
    )
    expiration_time = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        db_table = "order_products"
