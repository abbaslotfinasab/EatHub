from accounts.application.ports.user_registration_repository import (
    UserRegistrationRepository,
)
from accounts.application.registered_user import RegisteredUser


class RegistrationEmailAlreadyExistsError(Exception):
    """Raised when the requested email is already registered."""


class RegistrationNumberAlreadyExistsError(Exception):
    """Raised when the requested phone number is already registered."""


class RegisterUser:
    """Register a customer through the user-registration persistence port."""

    def __init__(self, repository: UserRegistrationRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        email: str,
        password: str,
        name: str,
        number: str,
    ) -> RegisteredUser:
        return self._repository.register_user(
            email=email,
            password=password,
            name=name,
            number=number,
        )
