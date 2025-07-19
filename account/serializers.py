from rest_framework import serializers
from .models import Seller, Deposite, Widraw
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError



class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ["id", "user", "balance"]


class UserDepositeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposite
        fields = [
            "amount",
        ]

    def validate_amount(self, amount):
        if amount < 0:
            raise ValidationError(detail="worng amount")


class AdminDepositeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposite
        fields = ["amount", "status", "seller", "timestamp"]


class UserWidrawSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widraw
        fields = ["amount", "phone"]

    def validate_amount(self, amount):
        if amount < 0:
            raise ValidationError(detail="worng amount")
