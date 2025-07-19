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
from rest_framework.permissions import IsAuthenticated
from django.db.models import F


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def user_deposit(request):
    serializer = UserDepositSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    seller = Seller.objects.get(user=request.user)
    Deposit.objects.create(amount=serializer.validated_data["amount"], seller=seller)
    return Response(
        {"detail": "inserted successfully witing for admin to approve it"},
        status=status.HTTP_200_OK,
    )


class AdminDepositView(
    mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    queryset = Deposit.objects.all()
    serializer_class = AdminDepositSerializer
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "PATCH method not allowed."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        with transaction.atomic():
            try:
                instance = Deposit.objects.get(pk=pk, status="pending")
            except Deposit.DoesNotExist:
                return Response(
                    {"detail": "Not found or not in pending status."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            instance.status = "approved"
            instance.save()
            Seller.objects.filter(id=instance.seller_id).update(
                balance=F("balance") + instance.amount
            )
            return Response(
                {"detail": "Deposit approved and seller balance updated."},
                status=status.HTTP_200_OK,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def charge_phone(request):
    serializer = UserWithdrawSerializer(request.data)
    serializer.is_valid(raise_exception=True)
    amount = serializer.validated_data["amount"]
    phone = serializer.validated_data["phone"]
    seller = Seller.objects.get(user=request.user)
    if amount > seller.balance:
        return Response(
            {"detail": "it;s more than your balance"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    with transaction.atomic():
        Seller.objects.filter(id=seller.id).update(balance=F("balance") - amount)
        Withdraw.objects.create(seller=seller, amount=amount, phone=phone)

        return Response(
            {"detail": "Deposit approved and seller balance updated."},
            status=status.HTTP_200_OK,
        )
