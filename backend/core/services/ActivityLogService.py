from core.models import ActivityLog


class ActivityLogService:
    @staticmethod
    def record(*, business, action, title, description, entity_type, entity_id, user=None):
        return ActivityLog.objects.create(
            business=business,
            user=user,
            action=action,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
        )
