from django.db import models
from django.conf import settings
from decimal import Decimal


class Account(models.Model):
    owner = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.CharField(max_length=80, unique=True, blank=False)
    balance = models.DecimalField(max_digits=19, decimal_places=7, default=Decimal(0))

    def __str__(self) -> str:
        return f"{self.owner} - {self.address}"
