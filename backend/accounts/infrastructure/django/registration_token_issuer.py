from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


class DjangoRegistrationTokenIssuer:
    """Issue the standard SimpleJWT pair for a newly registered user."""

    def issue(self, *, user_id: int) -> tuple[str, str]:
        user = User.objects.get(pk=user_id)
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh)
