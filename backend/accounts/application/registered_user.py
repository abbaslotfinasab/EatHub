from dataclasses import dataclass


@dataclass(frozen=True)
class RegisteredUser:
    user_id: int
    email: str
    name: str
    number: str
