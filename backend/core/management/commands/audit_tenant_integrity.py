import json

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F, Q


# Each rule compares tenant ownership across a relationship. scope_paths are
# used only to narrow the audit to rows touching the requested business.
RULES = (
    ("inventory.v1_stock_business_warehouse", "inventory.InventoryV1Stock",
     ~Q(business_id=F("warehouse__business_id")), ("business_id", "warehouse__business_id")),
    ("inventory.v1_stock_business_ingredient", "inventory.InventoryV1Stock",
     ~Q(business_id=F("ingredient__business_id")), ("business_id", "ingredient__business_id")),
    ("inventory.v1_movement_stock_business", "inventory.InventoryV1StockMovement",
     ~Q(business_id=F("stock__business_id")), ("business_id", "stock__business_id")),
    ("inventory.operation_warehouse_business", "inventory.InventoryOperation",
     ~Q(business_id=F("warehouse__business_id")), ("business_id", "warehouse__business_id")),
    ("inventory.operation_destination_business", "inventory.InventoryOperation",
     Q(destination_warehouse__isnull=False) & ~Q(business_id=F("destination_warehouse__business_id")),
     ("business_id", "destination_warehouse__business_id")),
    ("inventory.operation_line_ingredient_business", "inventory.InventoryOperationLine",
     ~Q(operation__business_id=F("ingredient__business_id")),
     ("operation__business_id", "ingredient__business_id")),
    ("inventory.reservation_warehouse_business", "inventory.InventoryReservation",
     ~Q(business_id=F("warehouse__business_id")), ("business_id", "warehouse__business_id")),
    ("inventory.reservation_line_ingredient_business", "inventory.InventoryReservationLine",
     ~Q(reservation__business_id=F("ingredient__business_id")),
     ("reservation__business_id", "ingredient__business_id")),
    ("inventory.legacy_stock_warehouse_ingredient", "inventory.Stock",
     ~Q(warehouse__business_id=F("ingredient__business_id")),
     ("warehouse__business_id", "ingredient__business_id")),
    ("inventory.recipe_input_ingredient_business", "inventory.RecipeInput",
     ~Q(recipe__business_id=F("ingredient__business_id")),
     ("recipe__business_id", "ingredient__business_id")),
    ("inventory.recipe_output_ingredient_business", "inventory.RecipeOutput",
     ~Q(recipe__business_id=F("ingredient__business_id")),
     ("recipe__business_id", "ingredient__business_id")),
    ("inventory.compound_component_business", "inventory.CompoundMaterialComponent",
     ~Q(compound__business_id=F("ingredient__business_id")),
     ("compound__business_id", "ingredient__business_id")),
    ("products.menu_item_menu_business", "products.MenuItem",
     ~Q(business_id=F("menu__business_id")), ("business_id", "menu__business_id")),
    ("products.menu_item_recipe_business", "products.MenuItem",
     Q(recipe__isnull=False) & ~Q(business_id=F("recipe__business_id")),
     ("business_id", "recipe__business_id")),
    ("products.order_customer_business", "products.Order",
     Q(customer__isnull=False) & ~Q(business_id=F("customer__business_id")),
     ("business_id", "customer__business_id")),
    ("products.order_item_menu_item_business", "products.OrderItem",
     Q(menu_item__isnull=False) & ~Q(order__business_id=F("menu_item__business_id")),
     ("order__business_id", "menu_item__business_id")),
    ("products.customer_account_business", "products.CustomerAccount",
     ~Q(business_id=F("customer__business_id")), ("business_id", "customer__business_id")),
    ("products.refund_order_business", "products.OrderRefund",
     ~Q(business_id=F("order__business_id")), ("business_id", "order__business_id")),
    ("products.refund_customer_business", "products.OrderRefund",
     Q(customer__isnull=False) & ~Q(business_id=F("customer__business_id")),
     ("business_id", "customer__business_id")),
    ("products.transaction_order_business", "products.CustomerTransaction",
     Q(order__isnull=False) & ~Q(account__business_id=F("order__business_id")),
     ("account__business_id", "order__business_id")),
    ("products.transaction_refund_business", "products.CustomerTransaction",
     Q(refund__isnull=False) & ~Q(account__business_id=F("refund__business_id")),
     ("account__business_id", "refund__business_id")),
    ("products.snapshot_order_business", "products.OrderItemRecipeSnapshot",
     ~Q(business_id=F("order__business_id")), ("business_id", "order__business_id")),
    ("products.snapshot_item_order", "products.OrderItemRecipeSnapshot",
     ~Q(order_id=F("order_item__order_id")), ("order_id", "order_item__order_id")),
    ("products.snapshot_recipe_business", "products.OrderItemRecipeSnapshot",
     ~Q(business_id=F("recipe__business_id")), ("business_id", "recipe__business_id")),
    ("products.snapshot_output_ingredient_business", "products.OrderItemRecipeSnapshot",
     ~Q(business_id=F("recipe_output_ingredient__business_id")),
     ("business_id", "recipe_output_ingredient__business_id")),
    ("products.requirement_ingredient_business", "products.OrderItemIngredientRequirement",
     ~Q(snapshot__business_id=F("ingredient__business_id")),
     ("snapshot__business_id", "ingredient__business_id")),
    ("products.consumption_order_business", "products.OrderInventoryConsumption",
     ~Q(business_id=F("order__business_id")), ("business_id", "order__business_id")),
    ("products.consumption_operation_business", "products.OrderInventoryConsumption",
     Q(inventory_operation__isnull=False) & ~Q(business_id=F("inventory_operation__business_id")),
     ("business_id", "inventory_operation__business_id")),
    ("products.consumption_line_requirement_business", "products.OrderInventoryConsumptionLine",
     ~Q(consumption__business_id=F("requirement__snapshot__business_id")),
     ("consumption__business_id", "requirement__snapshot__business_id")),
    ("products.consumption_line_movement_business", "products.OrderInventoryConsumptionLine",
     Q(inventory_movement__isnull=False) &
     ~Q(consumption__business_id=F("inventory_movement__business_id")),
     ("consumption__business_id", "inventory_movement__business_id")),
)


class Command(BaseCommand):
    help = (
        "Read-only audit of cross-business relationships in Inventory and Orders. "
        "This command never repairs or modifies data."
    )

    def add_arguments(self, parser):
        parser.add_argument("--business-id", type=int)
        parser.add_argument("--limit", type=int, default=1000)
        parser.add_argument("--fail-on-issues", action="store_true")

    def handle(self, *args, **options):
        business_id = options["business_id"]
        limit = options["limit"]
        if limit < 1:
            raise CommandError("--limit must be greater than zero.")
        if business_id is not None and business_id < 1:
            raise CommandError("--business-id must be greater than zero.")

        checked = {}
        issue_counts = {}
        issues = []
        issue_count = 0

        for rule_name, model_label, mismatch, scope_paths in RULES:
            model = apps.get_model(model_label)
            base_queryset = model._default_manager.all()
            if business_id is not None:
                scope = Q()
                for path in scope_paths:
                    scope |= Q(**{path: business_id})
                base_queryset = base_queryset.filter(scope)

            checked[rule_name] = base_queryset.count()
            queryset = base_queryset.filter(mismatch)
            count = queryset.count()
            issue_counts[rule_name] = count
            if count:
                remaining = max(0, limit - len(issues))
                if remaining:
                    rows = queryset.order_by("pk").values_list("pk", *scope_paths)[:remaining]
                    for row in rows:
                        issues.append({
                            "rule": rule_name,
                            "model": model_label,
                            "record_id": row[0],
                            "ownership": {
                                path: value for path, value in zip(scope_paths, row[1:])
                            },
                        })
                issue_count += count

        payload = {
            "scope": {"business_id": business_id},
            "read_only": True,
            "checked_rules": len(RULES),
            "checked_counts": checked,
            "issue_counts_by_rule": issue_counts,
            "issue_count": issue_count,
            "issues_returned": len(issues),
            "issues_truncated": issue_count > len(issues),
            "issues": issues,
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        if options["fail_on_issues"] and issue_count:
            raise CommandError(
                f"Tenant integrity audit found {issue_count} issue(s). "
                "No data was modified."
            )
