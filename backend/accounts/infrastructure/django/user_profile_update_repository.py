from accounts.application.update_user_profile import (
    UserProfileUpdatePersistenceResult,
)
from accounts.models import User


class DjangoUserProfileUpdateRepository:
    """Django ORM adapter for authenticated user profile updates."""

    def is_number_in_use(self, *, number: str, exclude_user_id: int) -> bool:
        return (
            User.objects.filter(number=number)
            .exclude(pk=exclude_user_id)
            .exists()
        )

    def update_profile(
        self, *, user_id: int, changes: dict[str, object]
    ) -> UserProfileUpdatePersistenceResult | None:
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            return None

        previous_avatar_path = user.avatar.name if user.avatar else None
        update_fields: list[str] = []
        for field in ("name", "number"):
            if field in changes:
                setattr(user, field, changes[field])
                update_fields.append(field)

        if "avatar_path" in changes:
            user.avatar = changes["avatar_path"]
            update_fields.append("avatar")

        if update_fields:
            user.save(update_fields=update_fields)

        return UserProfileUpdatePersistenceResult(
            previous_avatar_path=previous_avatar_path,
        )
