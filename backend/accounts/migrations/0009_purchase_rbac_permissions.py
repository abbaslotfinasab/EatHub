from django.db import migrations


PURCHASE_PERMISSIONS = {
    "purchase.view": "View Purchase Data",
    "purchase.requisition.view_own": "View Own Purchase Requisitions",
    "purchase.requisition.create": "Create Purchase Requisitions",
    "purchase.requisition.submit": "Submit Purchase Requisitions",
    "purchase.requisition.approve": "Approve or Reject Purchase Requisitions",
    "purchase.supplier.manage": "Manage Suppliers",
    "purchase.order.create": "Create Purchase Orders",
    "purchase.order.update": "Update Draft Purchase Orders",
    "purchase.order.dispatch": "Dispatch Purchase Orders",
    "purchase.order.cancel": "Cancel Purchase Orders",
    "purchase.receipt.create": "Create Goods Receipts",
    "purchase.invoice.create": "Create Purchase Invoices",
    "purchase.invoice.update": "Update Draft Purchase Invoices",
    "purchase.invoice.match": "Match Purchase Invoices",
    "purchase.invoice.approve": "Approve Purchase Invoices",
    "purchase.invoice.post": "Post Purchase Invoices",
    "purchase.invoice.cancel": "Cancel Purchase Invoices",
    "purchase.payment.create": "Create Supplier Payments",
    "purchase.payment.allocate": "Allocate Supplier Payments",
}

ROLE_GRANTS = {
    "MANAGER": {
        "purchase.view",
        "purchase.requisition.create",
        "purchase.requisition.submit",
        "purchase.supplier.manage",
        "purchase.order.create",
        "purchase.order.update",
        "purchase.receipt.create",
    },
    "CASHIER": {
        "purchase.requisition.view_own",
        "purchase.requisition.create",
        "purchase.requisition.submit",
    },
    "CHEF": {
        "purchase.requisition.view_own",
        "purchase.requisition.create",
        "purchase.requisition.submit",
    },
    "WAITER": {
        "purchase.requisition.view_own",
        "purchase.requisition.create",
        "purchase.requisition.submit",
    },
    "ACCOUNTANT": {
        "purchase.view",
        "purchase.invoice.create",
        "purchase.invoice.update",
        "purchase.invoice.match",
    },
}


def add_purchase_permissions(apps, schema_editor):
    Permission = apps.get_model("accounts", "Permission")
    Role = apps.get_model("accounts", "Role")
    RolePermission = apps.get_model("accounts", "RolePermission")

    permissions = {}
    for code, name in PURCHASE_PERMISSIONS.items():
        permission, _ = Permission.objects.using(schema_editor.connection.alias).get_or_create(
            code=code,
            defaults={"name": name},
        )
        permissions[code] = permission

    database = schema_editor.connection.alias
    for role_code, permission_codes in ROLE_GRANTS.items():
        roles = Role.objects.using(database).filter(
            code=role_code,
            is_system=True,
            business__isnull=False,
        )
        for role in roles.iterator():
            for permission_code in permission_codes:
                RolePermission.objects.using(database).get_or_create(
                    role_id=role.id,
                    permission_id=permissions[permission_code].id,
                )

    owner_permissions = Role.objects.using(database).filter(
        code="OWNER",
        is_system=True,
        business__isnull=False,
    )
    for role in owner_permissions.iterator():
        for permission in permissions.values():
            RolePermission.objects.using(database).get_or_create(
                role_id=role.id,
                permission_id=permission.id,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_remove_business_qr_code"),
    ]

    operations = [
        # Row ownership is not tracked. A destructive reverse could delete
        # pre-existing or subsequently assigned permissions, so this is
        # intentionally irreversible.
        migrations.RunPython(add_purchase_permissions),
    ]
