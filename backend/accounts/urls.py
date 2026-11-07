from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import (
    RegisterAPIView,
    BusinessInventorySettingsAPIView,
    LoginAPIView,
    SelectBusinessAPIView,
    MeAPIView,
    ChangePasswordAPIView,
    BusinessCreateAPIView,
    UserListAPIView,
)

app_name = "accounts"

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view()),
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/select-business/", SelectBusinessAPIView.as_view()),
    path("auth/me/", MeAPIView.as_view(), name="me"),
    path("auth/change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("create/business/", BusinessCreateAPIView.as_view()),
    path("business/inventory-settings/", BusinessInventorySettingsAPIView.as_view(), name="business-inventory-settings"),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("users/", UserListAPIView.as_view(), name="users"),
]
