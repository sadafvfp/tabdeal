from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from decimal import Decimal
from account.models import Seller, Deposit, Withdraw
from django.urls import reverse
from threading import Thread

USER_DEPOSIT_URL = reverse("user_deposit")
USER_WITHDRAW_URL = reverse("charge_phone")
LIST_ADMIN_DEPOSIT_URL = reverse("admin_deposit-list")


class DepositApprovalTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.seller = Seller.objects.create(user=self.user, balance=Decimal("1000"))
        self.deposit = Deposit.objects.create(
            seller=self.seller, amount=Decimal("200.00"), status="pending"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.admin = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)

    def test_successful_user_deposit(self):
        payload = {"amount": Decimal("500.00")}
        res = self.client.post(USER_DEPOSIT_URL, payload=payload)
        print(Deposit.objects.all())
        print(res.json())

    def test_successful_approval(self):
        url = f"/your-deposit-endpoint/{self.deposit.id}/deposit-approve/"
        response = self.client.post(url)
        self.seller.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Seller.objects.get(id=self.seller.id).balance, Decimal("1200.00")
        )
        self.assertEqual(Deposit.objects.get(id=self.deposit.id).status, "approved")

    def test_double_approval(self):
        url = f"/your-deposit-endpoint/{self.deposit.id}/deposit-approve/"

        # First call should succeed
        response1 = self.client.post(url)
        # Second call should fail
        response2 = self.client.post(url)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 400)  # or 409 depending on your logic
        self.assertEqual(
            Seller.objects.get(id=self.seller.id).balance, Decimal("1200.00")
        )


class ChargePhoneTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user2", password="pass")
        self.seller = Seller.objects.create(user=self.user, balance=Decimal("300.00"))
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_successful_charge(self):
        response = self.client.post(
            "/charge-phone/", data={"amount": 100, "phone": "09121234567"}
        )
        self.assertEqual(response.status_code, 200)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal("200.00"))
        self.assertEqual(Withdraw.objects.count(), 1)

    def test_insufficient_balance(self):
        response = self.client.post(
            "/charge-phone/", data={"amount": 400, "phone": "09121234567"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Withdraw.objects.count(), 0)
