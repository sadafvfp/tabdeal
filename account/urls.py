from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("", viewset=views.AdminDepositView, basename="admin_deposite")
urlpatterns = [
    path("deposit/", views.user_deposit, name="user_deposite"),
    path("charge-phone/", views.charge_phone, name="charge-phone"),
    path("admin/", include(router.urls)),
]
