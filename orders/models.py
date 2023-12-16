from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models.base import BaseNameModel


class Category(BaseNameModel):
    """Category"""

    sub_category = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
        related_name="categories",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        db_table = "order_categories"
