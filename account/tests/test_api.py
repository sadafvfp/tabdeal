from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from decimal import Decimal
from account.models import Seller, Deposit, Withdraw
from django.urls import reverse
from django.db.models import Sum

USER_DEPOSIT_URL = reverse("user_deposit")
USER_WITHDRAW_URL = reverse("charge_phone")
LIST_ADMIN_DEPOSIT_URL = reverse("admin_deposit-list")


def approve_deposit_url(pk):
    return reverse("admin_deposit-approve", kwargs={"pk": pk})


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
        data = {"amount": Decimal("500.00")}
        res = self.client.post(USER_DEPOSIT_URL, data=data)
        print(list(Deposit.objects.all().filter(id=1).values_list()))
        print(res.json())

    def test_successful_approval(self):
        url = approve_deposit_url(self.deposit.id)
        response = self.admin_client.post(url)
        self.seller.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Seller.objects.get(id=self.seller.id).balance, Decimal("1200.00")
        )
        self.assertEqual(Deposit.objects.get(id=self.deposit.id).status, "approved")

    def test_double_approval(self):
        url = approve_deposit_url(self.deposit.id)

        # First call should succeed
        response1 = self.admin_client.post(url)
        # Second call should fail
        response2 = self.admin_client.post(url)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 400)
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
            USER_WITHDRAW_URL, data={"amount": 100, "phone": "09121234567"}
        )
        self.assertEqual(response.status_code, 200)
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.balance, Decimal("200.00"))
        self.assertEqual(Withdraw.objects.count(), 1)

    def test_insufficient_balance(self):
        response = self.client.post(
            USER_WITHDRAW_URL, data={"amount": 400, "phone": "09121234567"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Withdraw.objects.count(), 0)


class CheckAtomocity(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.seller1 = Seller.objects.create(user=self.user1, balance=0)
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.seller2 = Seller.objects.create(
            user=self.user2, balance=Decimal("2000.00")
        )
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        self.admin = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)

    def test_deposit_and_withdraw_at_same_time(self):

        for _ in range(10):
            data1 = {"amount": Decimal("500.00")}
            data2 = {"amount": Decimal("10.00")}
            self.client1.post(USER_DEPOSIT_URL, data=data1)
            self.client2.post(USER_DEPOSIT_URL, data=data2)

        deposits = list(Deposit.objects.filter(status="pending"))
        for d in deposits:
            self.admin_client.post(approve_deposit_url(d.id))

        for _ in range(1000):
            self.client1.post(
                USER_WITHDRAW_URL, data={"amount": 1, "phone": "09121234567"}
            )
            self.client2.post(
                USER_WITHDRAW_URL, data={"amount": 1, "phone": "09121234567"}
            )
        for seller in [self.seller1, self.seller2]:
            intial_balance = seller.balance
            seller.refresh_from_db()
            print(seller.balance)

            total_deposit = Deposit.objects.filter(seller=seller).aggregate(
                Sum("amount")
            )["amount__sum"]
            print(total_deposit)
            total_spent = Withdraw.objects.filter(seller=seller).aggregate(
                Sum("amount")
            )["amount__sum"]
            print(total_spent)
            self.assertEqual(seller.balance, intial_balance+total_deposit - total_spent)
