from django.db import transaction
from django.contrib.auth import authenticate

from accounts.models import User
from accounts.services.business_service import BusinessService


class AuthService:

    # -------------------------
    # REGISTER (USER ONLY)
    # -------------------------
    @staticmethod
    @transaction.atomic
    def register(
        email: str,
        password: str,
        name: str,
        number: str,

    ):
        """
        فقط user ساخته میشه
        هیچ business ای اینجا ساخته نمیشه
        """

        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            number=number,

        )

        return user

    # -------------------------
    # LOGIN
    # -------------------------
    @staticmethod
    def login(email: str, password: str):

        user = authenticate(
            username=email,
            password=password
        )

        if not user:
            return None

        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True)
        )

        return {
            "user": user,
            "memberships": memberships
        }

    # -------------------------
    # ME (PROFILE CONTEXT)
    # -------------------------
    @staticmethod
    def get_profile(user):

        memberships = (
            user.memberships
            .select_related("business", "role")
            .filter(is_active=True)
        )

        return {
            "user": user,
            "memberships": memberships
        }

    # -------------------------
    # HAS ANY BUSINESS
    # -------------------------
    @staticmethod
    def has_business(user) -> bool:

        return user.memberships.filter(
            is_active=True
        ).exists()

    # -------------------------
    # CREATE FIRST BUSINESS
    # -------------------------
    @staticmethod
    def create_first_business(user, name: str):

        """
        onboarding step after register/login
        """

        return BusinessService.create_business(
            user=user,
            name=name
        )