from typing import Protocol

from accounts.application.registered_user import RegisteredUser


class UserRegistrationRepository(Protocol):
    """Persistence boundary for creating a customer account."""

    def register_user(
        self,
        *,
        email: str,
        password: str,
        name: str,
        number: str,
    ) -> RegisteredUser:
        ...
