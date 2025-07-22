from django.shortcuts import render
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from .models import Deposit, Withdraw, Seller
from .serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import F
from rest_framework.decorators import action


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_deposit(request):
    serializer = UserDepositSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    seller = Seller.objects.get(user=request.user)
    Deposit.objects.create(amount=serializer.validated_data["amount"], seller=seller)
    return Response(
        {"detail": "inserted successfully waiting for admin to approve it"},
        status=status.HTTP_200_OK,
    )


class AdminDepositView(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Deposit.objects.all()
    serializer_class = AdminDepositSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(methods=["POST"], detail=True, url_path="approve")
    def approve(self, request, *args, **kwargs):
        deposit = self.get_object()

        with transaction.atomic():

            result = self.queryset.filter(pk=deposit.id, status="pending").update(
                status="approved"
            )
            if result != 1:
                raise ValidationError("already approved")

            Seller.objects.filter(pk=deposit.seller_id).update(
                balance=F("balance") + deposit.amount
            )
            return Response(
                {"detail": "Deposit approved and seller balance updated."},
                status=status.HTTP_200_OK,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def charge_phone(request):
    serializer = UserWithdrawSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    amount = serializer.validated_data["amount"]
    phone = serializer.validated_data["phone"]

    seller = Seller.objects.get(user=request.user)
    with transaction.atomic():
        result = Seller.objects.filter(id=seller.id, balance__gt=amount).update(
            balance=F("balance") - amount
        )
        if result != 1:
            raise ValidationError("couldn't charge the provided phone number")
        Withdraw.objects.create(seller=seller, amount=amount, phone=phone)

        return Response(
            {"detail": "Phone charged and balance updated."},
            status=status.HTTP_200_OK,
        )
