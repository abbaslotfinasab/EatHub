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

        movements = InventoryV1StockMovement.objects.filter(
            source_type="goods_receipt",
        ).select_related("stock__warehouse", "stock__ingredient").order_by("pk")
        receipt_items = GoodsReceiptItem.objects.filter(
            received_quantity__gt=0,
        ).select_related(
            "receipt",
            "purchase_order_item__purchase_order__supplier",
        ).order_by("pk")
        links = GoodsReceiptInventoryMovementLink.objects.select_related(
            "receipt_item__receipt",
            "receipt_item__purchase_order_item__purchase_order__supplier",
            "movement__stock__warehouse",
            "movement__stock__ingredient",
        ).order_by("pk")

        business_id = options["business_id"]
        if business_id is not None:
            movements = movements.filter(business_id=business_id)
            receipt_items = receipt_items.filter(receipt__business_id=business_id)
            links = links.filter(receipt_item__receipt__business_id=business_id)

        issues = []

        def add_issue(code, *, movement_id=None, receipt_item_id=None, detail):
            issues.append({
                "code": code,
                "movement_id": movement_id,
                "receipt_item_id": receipt_item_id,
                "detail": detail,
            })

        movement_count = movements.count()
        receipt_item_count = receipt_items.count()
        link_count = links.count()

        for movement in movements.iterator():
            expected_item = receipt_items.filter(
                pk=movement.source_line_id,
                receipt_id=movement.source_document_id,
            ).first()
            link = links.filter(movement_id=movement.pk).first()

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

        for item in receipt_items.iterator():
            link = links.filter(receipt_item_id=item.pk).first()
            if link is None:
                add_issue(
                    "receipt_item_without_link",
                    receipt_item_id=item.pk,
                    detail="Receipt item has a positive received quantity but no explicit movement link.",
                )

        for link in links.iterator():
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
                "goods_receipt_movements": movement_count,
                "received_receipt_items": receipt_item_count,
                "links": link_count,
            },
            "issue_count": len(issues),
            "issues_truncated": len(issues) > limit,
            "issues": issues[:limit],
        }
        self.stdout.write(json.dumps(report, ensure_ascii=False, sort_keys=True))
        if issues and options["fail_on_issues"]:
            raise CommandError(
                f"Goods receipt trace audit found {len(issues)} issue(s)."
            )
