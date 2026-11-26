from django.contrib.auth import authenticate

from accounts.services.business_service import BusinessService


class AuthService:

    @staticmethod
    def login(identifier: str, password: str):
        return authenticate(username=identifier, password=password)

    @staticmethod
    def create_first_business(user, name: str):
        return BusinessService.create_business(user=user, name=name)
