from django.db.models import DecimalField


class BaseChoices:
    CHOICES = None

    @classmethod
    def name(cls, value):
        try:
            return dict(cls.CHOICES)[value]
        except KeyError:
            return None

    @classmethod
    def value(cls, name):
        try:
            return dict((v, k) for k, v in cls.CHOICES)[name]
        except KeyError:
            return None


class AmountField(DecimalField):
    """
    Override for set base max_digits, decimal_places and default values
    """

    def __init__(
        self,
        verbose_name=None,
        name=None,
        max_digits=10,
        decimal_places=2,
        **kwargs,
    ):
        if "default" not in kwargs:
            kwargs["default"] = 0.00
        super().__init__(
            verbose_name, name, max_digits, decimal_places, **kwargs
        )
