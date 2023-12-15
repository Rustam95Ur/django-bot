from core.models.model_fields import BaseChoices


class UserType(BaseChoices):
    """UserType"""

    CLIENT = 1
    ADMIN = 2

    CHOICES = (
        (CLIENT, "Client"),
        (ADMIN, "Admin"),
    )
