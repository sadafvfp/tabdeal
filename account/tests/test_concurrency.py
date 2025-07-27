from django.test import TestCase,TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from account.models import Seller, Deposit, Withdraw
from django.urls import reverse
from decimal import Decimal
import threading
from random import choice
from django.db import transaction, connection

USER_DEPOSIT_URL = reverse("user_deposit")
USER_WITHDRAW_URL = reverse("charge_phone")
LIST_ADMIN_DEPOSIT_URL = reverse("admin_deposit-list")


def approve_deposit_url(pk):
    return reverse("admin_deposit-approve", kwargs={"pk": pk})


class RaceConditionTest(TransactionTestCase):
    def setUp(self):
        # create users
        self.user1 = User.objects.create_user(username="seller1", password="test123")
        self.user2 = User.objects.create_user(username="seller2", password="test123")
        self.admin = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )

        # sellers
        self.seller1 = Seller.objects.create(
            user=self.user1, balance=Decimal("50000.00")
        )
        self.seller2 = Seller.objects.create(user=self.user2, balance=Decimal("0.00"))

        # clients
        self.client1 = APIClient()
        self.client2 = APIClient()
        self.client1.force_authenticate(self.user1)
        self.client2.force_authenticate(self.user2)

        # admin
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)

    def test_10_deposits_and_1000_concurrent_withdrawals(self):
     
        # 🔹 ایجاد 10 افزایش اعتبار برای seller1
        for _ in range(10):
            deposit = Deposit.objects.create(
                seller=self.seller1, amount=Decimal("1000.00"), status="pending"
            )
      

        # 🔹 تایید همزمان تمام افزایش اعتبارها
        deposits = list(Deposit.objects.filter(status="pending"))

        def approve_deposit(deposit):
            try:
                result = self.admin_client.post(approve_deposit_url(deposit.id))
                print(result.data)
            finally:
                # Force close the DB connection used by this thread
                connection.close()

        # for d in deposits:
        #     approve_deposit(d)

        threads = [threading.Thread(target=approve_deposit, args=[d]) for d in deposits]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 🔹 به‌روزرسانی seller1 و چک کردن نتیجه
        self.seller1.refresh_from_db()
        self.assertEqual(self.seller1.balance, Decimal("60000.00"))  # 50000 + 10 x 1000

        # 🔹 1000 فروش همزمان روی هر دو فروشنده
        # def withdraw_random_seller():
        #     seller, client = choice(
        #         [
        #             (self.seller1, self.client1),
        #             (self.seller2, self.client2),
        #         ]
        #     )
        #     url = reverse("charge-phone")
        #     data = {"amount": 10, "phone": "09121234567"}
        #     client.post(url, data, format="json")

        # threads = [threading.Thread(target=withdraw_random_seller) for _ in range(1000)]
        # for t in threads:
        #     t.start()
        # for t in threads:
        #     t.join()

        # # 🔹 بررسی تعداد برداشت‌ها
        # total_withdrawals = Withdraw.objects.count()
        # self.assertEqual(total_withdrawals, 1000)

        # # 🔹 اطمینان از اینکه موجودی هر فروشنده منفی نشده
        # self.seller1.refresh_from_db()
        # self.seller2.refresh_from_db()
        # self.assertGreaterEqual(self.seller1.balance, Decimal("0.00"))
        # self.assertGreaterEqual(self.seller2.balance, Decimal("0.00"))

        # # 🔹 اطمینان از صحت مجموع برداشت‌ها
        # total_balance_after = self.seller1.balance + self.seller2.balance
        # total_balance_before = Decimal("60000.00") + Decimal("50000.00")
        # total_withdrawn = total_balance_before - total_balance_after
        # self.assertEqual(total_withdrawn, Decimal("10000.00"))  # 1000 * 10 تومان
