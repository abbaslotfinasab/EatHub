from django.core.cache import cache


class RBACService:

    @staticmethod
    def _cache_key(role_id):
        return f"rbac:role:{role_id}"

    @staticmethod
    def get_role_permissions(role):
        key = RBACService._cache_key(role.id)

        permissions = cache.get(key)

        if permissions is None:
            permissions = set(
                role.rolepermission_set.values_list(
                    "permission__code",
                    flat=True
                )
            )
            cache.set(key, permissions, 3600)

        return permissions

    @staticmethod
    def has_permission(membership, permission):

        if not membership or not membership.is_active:
            return False

        permissions = RBACService.get_role_permissions(
            membership.role
        )

        return permission in permissions