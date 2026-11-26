from django.db import IntegrityError, transaction

from accounts.application.user_registration import (
    RegisteredUser,
    RegistrationEmailAlreadyExistsError,
    RegistrationNumberAlreadyExistsError,
)
from accounts.models import User


class DjangoUserRegistrationRepository:
    """Django ORM adapter for customer registration."""

    def register_user(
        self,
        *,
        email: str,
        password: str,
        name: str,
        number: str,
    ) -> RegisteredUser:
        if User.objects.filter(email=email).exists():
            raise RegistrationEmailAlreadyExistsError()
        if User.objects.filter(number=number).exists():
            raise RegistrationNumberAlreadyExistsError()

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    name=name,
                    number=number,
                )
        except IntegrityError:
            # Re-check after the failed transaction to handle concurrent
            # registrations that passed the initial uniqueness checks.
            if User.objects.filter(email=email).exists():
                raise RegistrationEmailAlreadyExistsError() from None
            if User.objects.filter(number=number).exists():
                raise RegistrationNumberAlreadyExistsError() from None
            raise

        return RegisteredUser(
            user_id=user.pk,
            email=user.email,
            name=user.name,
            number=user.number,
        )
