from django.urls import path

from accounts.views import (
    RegisterAPIView,
    LoginAPIView,
    SelectBusinessAPIView, MeAPIView,
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
]