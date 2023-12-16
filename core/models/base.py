import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """BaseModel"""

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class BaseUUIDModel(BaseModel):
    """BaseUUIDModel"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    class Meta:
        abstract = True


class BaseNameModel(BaseUUIDModel):
    """BaseNameModel"""

    name = models.CharField(verbose_name=_("Name"), unique=True, max_length=50)

    class Meta:
        abstract = True
