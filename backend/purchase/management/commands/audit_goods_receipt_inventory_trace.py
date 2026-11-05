import json

from django.core.management.base import BaseCommand, CommandError

from inventory.infrastructure.django.models import InventoryV1StockMovement
from purchase.models import GoodsReceiptInventoryMovementLink, GoodsReceiptItem


class Command(BaseCommand):
    help = (
        "Read-only audit of Goods Receipt to Inventory V1 movement trace integrity. "
        "Does not repair or mutate records."
    )

    def add_arguments(self, parser):
        parser.add_argument("--business-id", type=int, dest="business_id")
        parser.add_argument("--limit", type=int, default=1000)
        parser.add_argument("--fail-on-issues", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit < 1:
            raise CommandError("--limit must be greater than zero")

        movements_qs = InventoryV1StockMovement.objects.filter(
            source_type="goods_receipt",
        ).select_related("stock__warehouse", "stock__ingredient").order_by("pk")
        all_items_qs = GoodsReceiptItem.objects.select_related(
            "receipt",
            "purchase_order_item__purchase_order__supplier",
        ).order_by("pk")
        received_items_qs = all_items_qs.filter(received_quantity__gt=0)
        links_qs = GoodsReceiptInventoryMovementLink.objects.select_related(
            "receipt_item__receipt",
            "receipt_item__purchase_order_item__purchase_order__supplier",
            "movement__stock__warehouse",
            "movement__stock__ingredient",
        ).order_by("pk")

        business_id = options["business_id"]
        if business_id is not None:
            movements_qs = movements_qs.filter(business_id=business_id)
            all_items_qs = all_items_qs.filter(receipt__business_id=business_id)
            received_items_qs = received_items_qs.filter(
                receipt__business_id=business_id
            )
            links_qs = links_qs.filter(
                receipt_item__receipt__business_id=business_id
            )

        movements = list(movements_qs)
        all_items = list(all_items_qs)
        received_items = list(received_items_qs)
        links = list(links_qs)
        items_by_id = {item.pk: item for item in all_items}
        links_by_movement = {link.movement_id: link for link in links}
        links_by_item = {link.receipt_item_id: link for link in links}

        issues = []
        issue_count = 0

        def add_issue(code, *, movement_id=None, receipt_item_id=None, detail):
            nonlocal issue_count
            issue_count += 1
            if len(issues) < limit:
                issues.append({
                    "code": code,
                    "movement_id": movement_id,
                    "receipt_item_id": receipt_item_id,
                    "detail": detail,
                })

        for movement in movements:
            expected_item = items_by_id.get(movement.source_line_id)
            if (
                expected_item is not None
                and (
                    expected_item.receipt_id != movement.source_document_id
                    or expected_item.receipt.business_id != movement.business_id
                )
            ):
                expected_item = None

            link = links_by_movement.get(movement.pk)
            if expected_item is None:
                add_issue(
                    "movement_without_receipt_item",
                    movement_id=movement.pk,
                    detail="Source document/line does not resolve to a receipt item in the same business.",
                )
            if link is None:
                add_issue(
                    "movement_without_link",
                    movement_id=movement.pk,
                    receipt_item_id=expected_item.pk if expected_item else None,
                    detail="Goods receipt movement has no explicit protected link.",
                )
            elif expected_item is not None and link.receipt_item_id != expected_item.pk:
                add_issue(
                    "link_source_mismatch",
                    movement_id=movement.pk,
                    receipt_item_id=link.receipt_item_id,
                    detail="Link points to a receipt item different from movement source identity.",
                )

            if movement.operation_kind != "receive_stock":
                add_issue(
                    "movement_operation_mismatch",
                    movement_id=movement.pk,
                    receipt_item_id=expected_item.pk if expected_item else None,
                    detail="Goods receipt movement operation_kind is not receive_stock.",
                )
            if movement.movement_type != "receipt" or movement.direction != "in":
                add_issue(
                    "movement_type_direction_mismatch",
                    movement_id=movement.pk,
                    receipt_item_id=expected_item.pk if expected_item else None,
                    detail="Goods receipt movement must have movement_type=receipt and direction=in.",
                )

            stock = movement.stock
            if (
                stock.business_id != movement.business_id
                or stock.warehouse.business_id != movement.business_id
                or stock.ingredient.business_id != movement.business_id
            ):
                add_issue(
                    "movement_tenant_mismatch",
                    movement_id=movement.pk,
                    receipt_item_id=expected_item.pk if expected_item else None,
                    detail="Movement, stock, warehouse, or ingredient business scope differs.",
                )
            if expected_item is not None:
                order = expected_item.purchase_order_item.purchase_order
                if (
                    expected_item.purchase_order_item.ingredient_id != stock.ingredient_id
                    or order.business_id != movement.business_id
                    or order.supplier.business_id != movement.business_id
                ):
                    add_issue(
                        "receipt_purchase_inventory_mismatch",
                        movement_id=movement.pk,
                        receipt_item_id=expected_item.pk,
                        detail="Receipt item ingredient, purchase order, supplier, or movement tenant is inconsistent.",
                    )

        for item in received_items:
            if item.pk not in links_by_item:
                add_issue(
                    "receipt_item_without_link",
                    receipt_item_id=item.pk,
                    detail="Receipt item has a positive received quantity but no explicit movement link.",
                )

        for link in links:
            movement = link.movement
            item = link.receipt_item
            if (
                movement.source_type != "goods_receipt"
                or movement.operation_kind != "receive_stock"
                or movement.source_document_id != item.receipt_id
                or movement.source_line_id != item.pk
                or movement.business_id != item.receipt.business_id
            ):
                add_issue(
                    "link_movement_identity_mismatch",
                    movement_id=movement.pk,
                    receipt_item_id=item.pk,
                    detail="Linked movement source identity or business does not match its receipt item.",
                )

        report = {
            "scope": {"business_id": business_id},
            "checked": {
                "goods_receipt_movements": len(movements),
                "receipt_items": len(all_items),
                "received_receipt_items": len(received_items),
                "links": len(links),
            },
            "issue_count": issue_count,
            "issues_truncated": issue_count > len(issues),
            "issues": issues,
        }
        self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
        if issue_count and options["fail_on_issues"]:
            raise CommandError(
                f"Goods receipt trace audit found {issue_count} issue(s)."
            )
