from django.db import transaction
from django.contrib.auth import authenticate

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
        user = authenticate(username=identifier, password=password)
        if not user:
            return None

        # Return every business the user belongs to, not only the active one.
        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True, business__is_active=True)
            .order_by("business__name")
        )
        return {"user": user, "memberships": memberships}

    @staticmethod
    def get_profile(user):
        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True, business__is_active=True)
            .order_by("business__name")
        )
        return {"user": user, "memberships": memberships}

    @staticmethod
    def has_business(user) -> bool:
        return user.memberships.filter(is_active=True, business__is_active=True).exists()

    @staticmethod
    def create_first_business(user, name: str):
        return BusinessService.create_business(user=user, name=name)
