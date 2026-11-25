from django.contrib.auth import authenticate
from django.db import transaction

from accounts.models import User
from accounts.services.business_service import BusinessService


class AuthService:

    @staticmethod
    @transaction.atomic
    def register(email: str, password: str, name: str, number: str):
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            number=number,
        )
        return user

    @staticmethod
    def login(identifier: str, password: str):
        return authenticate(username=identifier, password=password)

    @staticmethod
    def create_first_business(user, name: str):
        return BusinessService.create_business(user=user, name=name)
