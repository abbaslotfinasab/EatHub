from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    email: str
    name: str
    number: str
