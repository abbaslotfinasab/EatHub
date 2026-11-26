from django.db import transaction

from accounts.models import User


class DjangoPasswordChangeRepository:
    """Django adapter for verifying and persisting password changes."""

    @transaction.atomic
    def change_password(
        self,
        *,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> bool | None:
        user = User.objects.select_for_update().filter(pk=user_id).first()
        if user is None:
            return None
        if not user.check_password(old_password):
            return False

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return True
