from rest_framework import serializers
from .models import Seller, Deposit, Withdraw
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError


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
        if amount < 0:
            raise ValidationError(detail="worng amount")


class AdminDepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ["amount", "status", "seller", "timestamp"]


class UserWithdrawSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdraw
        fields = ["amount", "phone"]

    def validate_amount(self, amount):
        if amount < 0:
            raise ValidationError(detail="worng amount")
