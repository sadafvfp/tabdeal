from django.db import models
from django.contrib.auth.models import User


TRANSACTION_TYPES = [
    ("pending", "pending"),
    ("approved", "approved"),
    ("rejected", "rejected"),
]


class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Deposit(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=TRANSACTION_TYPES, default="pending"
    )
    seller = models.ForeignKey(Seller, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True)


class Withdraw(models.Model):
    phone = models.CharField(max_length=11)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    seller = models.ForeignKey(Seller, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField(auto_now_add=True)
