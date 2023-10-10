from django.db import models


class BaseModel(models.Model):
    """BaseModel"""

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class BaseIdModel(BaseModel):
    """BaseIdModel"""

    id = models.IntegerField(
        primary_key=True,
        editable=False,
        unique=True,
    )

    class Meta:
        abstract = True



