# accounts/services/rbac_initializer.py
from accounts.constants import ALL_PERMISSIONS
from accounts.enums import RoleCode
from accounts.models import (
    Role,
    Permission,
    RolePermission,
)
from core.enums import PermissionCode
from django.db import transaction

ROLE_PERMISSIONS = {

    RoleCode.OWNER: list(PermissionCode),

    RoleCode.MANAGER: [
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_CREATE,
        PermissionCode.PRODUCTS_UPDATE,

        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
        PermissionCode.ORDERS_UPDATE,
        PermissionCode.PAYMENTS_MANAGE,

        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_ADJUST,
        PermissionCode.INVENTORY_ORDER_FULFILL,
        PermissionCode.INVENTORY_ITEM_MANAGE,
        PermissionCode.INVENTORY_WAREHOUSE_MANAGE,
        PermissionCode.INVENTORY_RECIPE_MANAGE,
        PermissionCode.INVENTORY_COMPOUND_MANAGE,

        PermissionCode.PURCHASE_VIEW,
        PermissionCode.PURCHASE_REQUISITION_CREATE,
        PermissionCode.PURCHASE_REQUISITION_SUBMIT,
        PermissionCode.PURCHASE_SUPPLIER_MANAGE,
        PermissionCode.PURCHASE_ORDER_CREATE,
        PermissionCode.PURCHASE_ORDER_UPDATE,
        PermissionCode.PURCHASE_RECEIPT_CREATE,

        PermissionCode.REPORTS_VIEW_SALES,
    ],

    RoleCode.CASHIER: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
        PermissionCode.PURCHASE_REQUISITION_VIEW_OWN,
        PermissionCode.PURCHASE_REQUISITION_CREATE,
        PermissionCode.PURCHASE_REQUISITION_SUBMIT,
    ],

    RoleCode.CHEF: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_UPDATE,
        PermissionCode.INVENTORY_ORDER_FULFILL,
        PermissionCode.PURCHASE_REQUISITION_VIEW_OWN,
        PermissionCode.PURCHASE_REQUISITION_CREATE,
        PermissionCode.PURCHASE_REQUISITION_SUBMIT,
    ],

    RoleCode.WAITER: [
        PermissionCode.ORDERS_VIEW,
        PermissionCode.ORDERS_CREATE,
        PermissionCode.PURCHASE_REQUISITION_VIEW_OWN,
        PermissionCode.PURCHASE_REQUISITION_CREATE,
        PermissionCode.PURCHASE_REQUISITION_SUBMIT,
    ],

    RoleCode.ACCOUNTANT: [
        PermissionCode.REPORTS_VIEW_SALES,
        PermissionCode.PAYMENTS_MANAGE,
        PermissionCode.PURCHASE_VIEW,
        PermissionCode.PURCHASE_INVOICE_CREATE,
        PermissionCode.PURCHASE_INVOICE_UPDATE,
        PermissionCode.PURCHASE_INVOICE_MATCH,
    ],
}


class RBACInitializer:

    @staticmethod
    @transaction.atomic
    def initialize(business):

        reserved_role_codes = [role_code.value for role_code in ROLE_PERMISSIONS]
        conflicting_roles = list(
            Role.objects.filter(
                business=business,
                code__in=reserved_role_codes,
                is_system=False,
            ).values_list("code", flat=True)
        )
        if conflicting_roles:
            codes = ", ".join(sorted(conflicting_roles))
            raise ValueError(
                f"Cannot initialize default roles; non-system roles use reserved codes: {codes}."
            )

        required_permission_codes = set()
        for permission_codes in ROLE_PERMISSIONS.values():
            if permission_codes == "__all__":
                required_permission_codes.update(permission.value for permission in PermissionCode)
            else:
                required_permission_codes.update(
                    permission.value if isinstance(permission, PermissionCode) else permission
                    for permission in permission_codes
                )

        permission_labels = {
            permission.value: permission.label
            for permission in PermissionCode
        }
        permissions_by_code = {}
        for permission_code in required_permission_codes:
            permission, _ = Permission.objects.get_or_create(
                code=permission_code,
                defaults={"name": permission_labels.get(permission_code, permission_code)},
            )
            permissions_by_code[permission_code] = permission

        for role_code, permission_codes in ROLE_PERMISSIONS.items():

            role, _ = Role.objects.get_or_create(
                business=business,
                code=role_code,
                name=role_code.label,
                is_system=True
            )

            if not role.is_system:
                raise ValueError(
                    f"Cannot initialize default role {role.code}; it is not a system role."
                )

            role_permission_codes = (
                [permission.value for permission in PermissionCode]
                if permission_codes == "__all__"
                else [
                    permission.value if isinstance(permission, PermissionCode) else permission
                    for permission in permission_codes
                ]
            )
            for permission_code in role_permission_codes:
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permissions_by_code[permission_code],
                )
