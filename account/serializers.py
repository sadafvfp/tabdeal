from rest_framework import serializers
from .models import Seller, Deposit, Withdraw
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.core.validators import RegexValidator


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ["id", "user", "balance"]


class UserDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = [
            "amount",
        ]

    def validate_amount(self, amount):
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        return amount


class AdminDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ["id", "amount", "status", "seller", "timestamp"]


class UserWithdrawSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(
        validators=[RegexValidator(regex=r"^09\d{9}$", message="Invalid phone number.")]
    )

    class Meta:
        model = Withdraw
        fields = ["amount", "phone"]

    def validate_amount(self, amount):
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        return amount
