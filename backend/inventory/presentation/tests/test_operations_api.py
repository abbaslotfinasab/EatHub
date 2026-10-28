from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import InventoryOperation, InventoryV1Stock, InventoryV1StockMovement
from inventory.models import Ingredient, Warehouse


class InventoryOperationsAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Operations business")
        self.other_business = Business.objects.create(name="Other operations business")
        self.view_permission = Permission.objects.create(code=PermissionCode.INVENTORY_VIEW.value, name="View Inventory")
        self.adjust_permission = Permission.objects.create(code=PermissionCode.INVENTORY_ADJUST.value, name="Adjust Inventory")
        self.owner = self._member(self.business, "ops-owner", (self.view_permission, self.adjust_permission))
        self.viewer = self._member(self.business, "ops-viewer", (self.view_permission,), role_code="VIEWER")
        self.other_owner = self._member(self.other_business, "ops-other", (self.view_permission, self.adjust_permission))
        self.item = Ingredient.objects.create(business=self.business, name="Rice", unit="kg")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.destination = Warehouse.objects.create(business=self.business, name="Cold store")
        self.foreign_warehouse = Warehouse.objects.create(business=self.other_business, name="Foreign")
        self.stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.item,
            unit="kg", quantity=Decimal("10"), average_cost=Decimal("4"),
        )
        self.client.force_authenticate(self.owner)

    @staticmethod
    def _member(business, suffix, permissions, role_code="OWNER"):
        role = Role.objects.create(business=business, name=role_code, code=f"{role_code}-{suffix}")
        for permission in permissions:
            RolePermission.objects.create(role=role, permission=permission)
        user = User.objects.create_user(
            email=f"{suffix}@example.test", password="unused-test-password",
            name=suffix, number=f"op-{suffix}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def _create(self, endpoint, data):
        response = self.client.post(endpoint, data, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_issue_posts_once_and_insufficient_stock_rolls_back(self):
        issue = self._create("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Kitchen use",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "3", "unit": "kg"}],
        })
        posted = self.client.post(f"/api/inventory/issues/{issue['id']}/post/", {}, format="json")
        self.assertEqual(posted.status_code, 200, posted.data)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.stock.pk).quantity, Decimal("7"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="issue").count(), 1)
        repeated = self.client.post(f"/api/inventory/issues/{issue['id']}/post/", {}, format="json")
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="issue").count(), 1)
        reversed_response = self.client.post(f"/api/inventory/issues/{issue['id']}/reverse/", {}, format="json")
        self.assertEqual(reversed_response.status_code, 200, reversed_response.data)
        self.assertEqual(reversed_response.data["status"], "reversed")
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="reversal").count(), 1)
        repeated_reverse = self.client.post(f"/api/inventory/issues/{issue['id']}/reverse/", {}, format="json")
        self.assertEqual(repeated_reverse.status_code, 200)
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="reversal").count(), 1)

        too_much = self._create("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Over issue",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "99", "unit": "kg"}],
        })
        response = self.client.post(f"/api/inventory/issues/{too_much['id']}/post/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="issue").count(), 1)

    def test_multi_line_issue_rolls_back_all_movements_when_one_line_is_short(self):
        second_item = Ingredient.objects.create(business=self.business, name="Beans", unit="kg")
        second_stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=second_item,
            unit="kg", quantity=Decimal("1"), average_cost=Decimal("2"),
        )
        issue = self._create("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Meal service",
            "lines": [
                {"ingredient_id": self.item.pk, "quantity": "2", "unit": "kg"},
                {"ingredient_id": second_item.pk, "quantity": "2", "unit": "kg"},
            ],
        })
        response = self.client.post(f"/api/inventory/issues/{issue['id']}/post/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1Stock.objects.get(pk=second_stock.pk).quantity, Decimal("1"))
        self.assertFalse(InventoryV1StockMovement.objects.filter(movement_type="issue").exists())
    def test_transfer_has_explicit_in_transit_then_receives_once(self):
        transfer = self._create("/api/inventory/transfers/", {
            "warehouse_id": self.warehouse.pk, "destination_warehouse_id": self.destination.pk,
            "reference": "MOVE-1",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "2", "unit": "kg"}],
        })
        dispatched = self.client.post(f"/api/inventory/transfers/{transfer['id']}/dispatch/", {}, format="json")
        self.assertEqual(dispatched.status_code, 200, dispatched.data)
        self.assertEqual(dispatched.data["status"], "in_transit")
        self.assertEqual(dispatched.data["lines"][0]["in_transit_quantity"], "2.000000000000")
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.stock.pk).quantity, Decimal("8"))
        self.client.post(f"/api/inventory/transfers/{transfer['id']}/dispatch/", {}, format="json")
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="transfer_dispatch").count(), 1)
        received = self.client.post(f"/api/inventory/transfers/{transfer['id']}/receive/", {}, format="json")
        self.assertEqual(received.status_code, 200, received.data)
        self.assertEqual(received.data["status"], "received")
        self.assertEqual(InventoryV1Stock.objects.get(warehouse=self.destination).quantity, Decimal("2"))
        self.client.post(f"/api/inventory/transfers/{transfer['id']}/receive/", {}, format="json")
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type__startswith="transfer_").count(), 2)

    def test_stocktake_uses_snapshot_and_rejects_stale_approval(self):
        stocktake = self._create("/api/inventory/stocktakes/", {
            "warehouse_id": self.warehouse.pk,
            "lines": [{"ingredient_id": self.item.pk, "quantity": "0", "unit": "kg"}],
        })
        line = stocktake["lines"][0]
        counted = self.client.patch(f"/api/inventory/stocktakes/{stocktake['id']}/", {
            "lines": [{"id": line["id"], "counted_quantity": "8"}],
        }, format="json")
        self.assertEqual(counted.status_code, 200, counted.data)
        InventoryV1Stock.objects.filter(pk=self.stock.pk).update(quantity=Decimal("9"))
        stale = self.client.post(f"/api/inventory/stocktakes/{stocktake['id']}/approve/", {}, format="json")
        self.assertEqual(stale.status_code, 409, stale.data)
        self.assertFalse(InventoryV1StockMovement.objects.filter(source_type="inventory_stocktake").exists())

    def test_stocktake_requires_cost_when_count_adds_quantity_to_zero_cost_stock(self):
        zero_stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.destination, ingredient=self.item,
            unit="kg", quantity=Decimal("0"), average_cost=Decimal("0"),
        )
        stocktake = self._create("/api/inventory/stocktakes/", {
            "warehouse_id": self.destination.pk,
            "lines": [{"ingredient_id": self.item.pk, "quantity": "0", "unit": "kg"}],
        })
        line = stocktake["lines"][0]
        counted = self.client.patch(f"/api/inventory/stocktakes/{stocktake['id']}/", {
            "lines": [{"id": line["id"], "counted_quantity": "2"}],
        }, format="json")
        self.assertEqual(counted.status_code, 200, counted.data)
        missing_cost = self.client.post(f"/api/inventory/stocktakes/{stocktake['id']}/approve/", {}, format="json")
        self.assertEqual(missing_cost.status_code, 400)
        self.assertEqual(InventoryV1Stock.objects.get(pk=zero_stock.pk).quantity, Decimal("0"))
        self.assertFalse(InventoryV1StockMovement.objects.filter(source_type="inventory_stocktake").exists())
        counted = self.client.patch(f"/api/inventory/stocktakes/{stocktake['id']}/", {
            "lines": [{"id": line["id"], "counted_quantity": "2", "counted_unit_cost": "5"}],
        }, format="json")
        self.assertEqual(counted.status_code, 200, counted.data)
        approved = self.client.post(f"/api/inventory/stocktakes/{stocktake['id']}/approve/", {}, format="json")
        self.assertEqual(approved.status_code, 200, approved.data)
        self.assertEqual(InventoryV1Stock.objects.get(pk=zero_stock.pk).average_cost, Decimal("5"))
        self.client.post(f"/api/inventory/stocktakes/{stocktake['id']}/approve/", {}, format="json")
        self.assertEqual(InventoryV1StockMovement.objects.filter(source_type="inventory_stocktake").count(), 1)

    def test_tenant_isolation_and_permissions_apply_to_documents_and_history(self):
        foreign = self._create("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Own item",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg"}],
        })
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.get(f"/api/inventory/issues/{foreign['id']}/").status_code, 404)
        self.assertEqual(self.client.get("/api/inventory/movements/").status_code, 200)
        self.client.force_authenticate(self.viewer)
        denied = self.client.post(f"/api/inventory/issues/{foreign['id']}/post/", {}, format="json")
        self.assertEqual(denied.status_code, 403)

    def test_view_permission_can_list_but_cannot_create_or_post(self):
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/inventory/issues/").status_code, 200)
        denied = self.client.post("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Not allowed",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg"}],
        }, format="json")
        self.assertEqual(denied.status_code, 403)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/inventory/movements/").status_code, 401)

    def test_movement_history_is_business_scoped_and_filterable(self):
        issue = self._create("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Waste",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg"}],
        })
        self.client.post(f"/api/inventory/issues/{issue['id']}/post/", {}, format="json")
        history = self.client.get("/api/inventory/movements/?movement_type=issue&warehouse_id=%s" % self.warehouse.pk)
        self.assertEqual(history.status_code, 200, history.data)
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(history.data["results"][0]["balance_after"], "9.000000000000")
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.get("/api/inventory/movements/").data["count"], 0)

    def test_transfer_rejects_foreign_warehouse_and_unknown_tenant_fields(self):
        response = self.client.post("/api/inventory/transfers/", {
            "warehouse_id": self.warehouse.pk, "destination_warehouse_id": self.foreign_warehouse.pk,
            "business_id": self.other_business.pk,
            "lines": [{"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg"}],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(InventoryOperation.objects.count(), 0)

    def test_client_cannot_supply_business_or_actor_identity(self):
        response = self.client.post("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk, "reason": "Kitchen use",
            "business_id": self.other_business.pk, "created_by_id": self.other_owner.pk,
            "lines": [{"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg"}],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(InventoryOperation.objects.count(), 0)
