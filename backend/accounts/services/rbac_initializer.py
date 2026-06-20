# accounts/services/rbac_initializer.py
from accounts.constants import ALL_PERMISSIONS
from accounts.enums import RoleCode
from accounts.models import (
    Role,
    Permission,
    RolePermission,
)
from core.enums import PermissionCode

ROLE_PERMISSIONS = {

    RoleCode.OWNER: list(PermissionCode),

    RoleCode.MANAGER: [
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_CREATE,
        PermissionCode.PRODUCTS_UPDATE,

        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
        PermissionCode.ORDERS_UPDATE,

        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_ADJUST,

        PermissionCode.REPORTS_VIEW_SALES,
    ],

    RoleCode.CASHIER: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
    ],

    RoleCode.CHEF: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_UPDATE,
    ],

    RoleCode.WAITER: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
    ],

    RoleCode.ACCOUNTANT: [
        PermissionCode.REPORTS_VIEW_SALES,
    ],
}


class RBACInitializer:

    @staticmethod
    def initialize(business):

        for role_code, permission_codes in ROLE_PERMISSIONS.items():

            role, _ = Role.objects.get_or_create(
                business=business,
                code=role_code,
                name=role_code.label,
                is_system=True
            )

            if permission_codes == "__all__":
                permissions = Permission.objects.all()

            else:
                permissions = Permission.objects.filter(
                    code__in=permission_codes
                )

            role_permissions = [
                RolePermission(
                    role=role,
                    permission=permission
                )
                for permission in permissions
            ]

            RolePermission.objects.bulk_create(
                role_permissions
            )