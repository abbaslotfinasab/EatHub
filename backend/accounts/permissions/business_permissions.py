from rest_framework.permissions import BasePermission

from accounts.services.rbac_service import RBACService


class HasBusinessPermission(BasePermission):

    required_permission = None  # override in views

    def has_permission(self, request, view):

        # must have tenant
        if not getattr(request, "business", None):
            return False

        # must have membership
        if not getattr(request, "membership", None):
            return False

        permission = getattr(
            view,
            "required_permission",
            self.required_permission
        )

        if not permission:
            return True  # no restriction

        return RBACService.has_permission(
            membership=request.membership,
            permission=permission
        )