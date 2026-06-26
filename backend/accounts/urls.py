from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import (
    RegisterAPIView,
    LoginAPIView,
    SelectBusinessAPIView, MeAPIView, BusinessCreateAPIView, UserListAPIView,
)

app_name = 'accounts'

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view()),
    path("auth/login/", LoginAPIView.as_view()),
    path("auth/select-business/", SelectBusinessAPIView.as_view()),

    path(
        "auth/me/",
        MeAPIView.as_view(),
        name="me"
    ),

    path("create/business/", BusinessCreateAPIView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),

    path(
        "users/",
        UserListAPIView.as_view(),
        name="users"
    ),

]