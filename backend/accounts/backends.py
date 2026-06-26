from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from accounts.models import User


class EmailOrPhoneBackend(ModelBackend):

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs
    ):
        if not username or not password:
            return None

        user = (
            User.objects
            .filter(
                Q(email__iexact=username) |
                Q(number=username)
            )
            .first()
        )

        if not user:
            return None

        if not user.check_password(password):
            return None

        if not self.user_can_authenticate(user):
            return None

        return user