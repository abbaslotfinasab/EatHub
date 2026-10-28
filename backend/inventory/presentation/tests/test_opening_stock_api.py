from decimal import Decimal

from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import InventoryOperation, InventoryV1Stock, InventoryV1StockMovement
from inventory.models import Ingredient, Warehouse


class OpeningStockAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Opening stock business")
        self.other_business = Business.objects.create(name="Other opening business")
        self.view_permission = Permission.objects.create(code=PermissionCode.INVENTORY_VIEW.value, name="View Inventory")
        self.adjust_permission = Permission.objects.create(code=PermissionCode.INVENTORY_ADJUST.value, name="Adjust Inventory")
        self.owner = self._member(self.business, "opening-owner", (self.view_permission, self.adjust_permission))
        self.viewer = self._member(self.business, "opening-viewer", (self.view_permission,), role_code="VIEWER")
        self.other_owner = self._member(self.other_business, "opening-other", (self.view_permission, self.adjust_permission))
        self.item = Ingredient.objects.create(business=self.business, name="Rice", unit="kg")
        self.second_item = Ingredient.objects.create(business=self.business, name="Beans", unit="g")
        self.inactive_item = Ingredient.objects.create(business=self.business, name="Inactive", unit="pc", is_active=False)
        self.foreign_item = Ingredient.objects.create(business=self.other_business, name="Foreign", unit="kg")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.foreign_warehouse = Warehouse.objects.create(business=self.other_business, name="Foreign")
        self.client.force_authenticate(self.owner)

    @staticmethod
    def _member(business, suffix, permissions, role_code="OWNER"):
        role = Role.objects.create(business=business, name=role_code, code=f"{role_code}-{suffix}")
        for permission in permissions:
            RolePermission.objects.create(role=role, permission=permission)
        user = User.objects.create_user(
            email=f"{suffix}@example.test", password="unused-test-password",
            name=suffix, number=f"ob-{suffix}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def _payload(self, lines=None, **changes):
        data = {
            "warehouse_id": self.warehouse.pk,
            "reference": "INITIAL-001",
            "reason": "Opening count",
            "lines": lines or [{"ingredient_id": self.item.pk, "quantity": "2.5", "unit": "kg", "unit_cost": "4.25"}],
        }
        data.update(changes)
        return data

    def test_opening_entry_records_multiple_movements_and_visible_projection(self):
        response = self.client.post("/api/inventory/opening-stock/", self._payload([
            {"ingredient_id": self.item.pk, "quantity": "2.5", "unit": "kg", "unit_cost": "4.25"},
            {"ingredient_id": self.second_item.pk, "quantity": "500", "unit": "g", "unit_cost": "1.75"},
        ]), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["status"], "posted")
        self.assertEqual(InventoryOperation.objects.get(pk=response.data["id"]).operation_type, "opening_stock")
        self.assertEqual(InventoryV1Stock.objects.get(ingredient=self.item).quantity, Decimal("2.5"))
        self.assertEqual(InventoryV1Stock.objects.get(ingredient=self.second_item).quantity, Decimal("500"))
        movements = InventoryV1StockMovement.objects.filter(movement_type="opening_balance")
        self.assertEqual(movements.count(), 2)
        self.assertEqual(set(movements.values_list("source_type", flat=True)), {"inventory_opening_stock"})
        history = self.client.get("/api/inventory/movements/?movement_type=opening_balance")
        self.assertEqual(history.status_code, 200, history.data)
        self.assertEqual(history.data["count"], 2)
        balances = self.client.get(f"/api/inventory/balances/?ingredient_id={self.item.pk}")
        self.assertEqual(balances.status_code, 200, balances.data)
        self.assertEqual(balances.data["results"][0]["quantity"], "2.500000000000")
        self.assertEqual(InventoryV1Stock.objects.get(ingredient=self.item).average_cost, Decimal("4.25"))

    def test_valid_single_line_payload_passes_nested_serializer_validation(self):
        response = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["lines"]), 1)

    def test_unexpected_fields_are_rejected_at_top_level_and_nested_line(self):
        nested_payload = self._payload()
        nested_payload["lines"][0]["unexpected_line_field"] = "nope"
        nested_response = self.client.post(
            "/api/inventory/opening-stock/", nested_payload, format="json"
        )
        self.assertEqual(nested_response.status_code, 400, nested_response.data)
        self.assertIn("unexpected_line_field", nested_response.data["lines"][0])

        top_level_payload = self._payload()
        top_level_payload["unexpected_top_level_field"] = "nope"
        top_level_response = self.client.post(
            "/api/inventory/opening-stock/", top_level_payload, format="json"
        )
        self.assertEqual(top_level_response.status_code, 400, top_level_response.data)
        self.assertIn("unexpected_top_level_field", top_level_response.data)

    def test_opening_quantity_is_converted_to_canonical_unit_without_changing_cost_basis(self):
        response = self.client.post("/api/inventory/opening-stock/", self._payload([
            {"ingredient_id": self.item.pk, "quantity": "1250", "unit": "g", "unit_cost": "4.25"},
        ]), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        stock = InventoryV1Stock.objects.get(ingredient=self.item)
        movement = InventoryV1StockMovement.objects.get(movement_type="opening_balance")
        self.assertEqual(stock.unit, "kg")
        self.assertEqual(stock.quantity, Decimal("1.250"))
        self.assertEqual(stock.average_cost, Decimal("4.25"))
        self.assertEqual(movement.unit, "kg")
        self.assertEqual(movement.quantity, Decimal("1.250"))
        self.assertEqual(movement.unit_cost, Decimal("4.25"))

    def test_explicit_zero_cost_initializes_zero_valuation(self):
        response = self.client.post("/api/inventory/opening-stock/", self._payload([
            {"ingredient_id": self.item.pk, "quantity": "2", "unit": "kg", "unit_cost": "0"},
        ]), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        stock = InventoryV1Stock.objects.get(ingredient=self.item)
        movement = InventoryV1StockMovement.objects.get(movement_type="opening_balance")
        self.assertEqual(stock.quantity, Decimal("2"))
        self.assertEqual(stock.average_cost, Decimal("0"))
        self.assertEqual(movement.unit_cost, Decimal("0"))

    def test_second_opening_is_rejected_after_stock_returns_to_zero(self):
        opened = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(opened.status_code, 201, opened.data)
        issue = self.client.post("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk,
            "reason": "Consume all stock",
            "lines": [{"ingredient_id": self.item.pk, "quantity": "2.5", "unit": "kg"}],
        }, format="json")
        self.assertEqual(issue.status_code, 201, issue.data)
        posted = self.client.post(f"/api/inventory/issues/{issue.data['id']}/post/", {}, format="json")
        self.assertEqual(posted.status_code, 200, posted.data)
        stock = InventoryV1Stock.objects.get(ingredient=self.item)
        self.assertEqual(stock.quantity, Decimal("0"))
        self.assertEqual(stock.average_cost, Decimal("0"))
        self.assertTrue(InventoryV1StockMovement.objects.filter(stock=stock).exists())
        retry = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(retry.status_code, 409, retry.data)
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="opening_balance").count(), 1)

    def test_opening_document_detail_returns_audit_metadata_and_is_business_scoped(self):
        created = self.client.post("/api/inventory/opening-stock/", self._payload(notes="Counted before launch"), format="json")
        self.assertEqual(created.status_code, 201, created.data)
        endpoint = f"/api/inventory/opening-stock/{created.data['id']}/"
        detail = self.client.get(endpoint)
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertEqual(detail.data["reference"], "INITIAL-001")
        self.assertEqual(detail.data["reason"], "Opening count")
        self.assertEqual(detail.data["notes"], "Counted before launch")
        self.assertEqual(len(detail.data["lines"]), 1)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(endpoint).status_code, 200)
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.get(endpoint).status_code, 404)

    def test_rejects_duplicates_invalid_values_missing_cost_and_incompatible_units(self):
        duplicate = self._payload([
            {"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg", "unit_cost": "2"},
            {"ingredient_id": self.item.pk, "quantity": "1", "unit": "kg", "unit_cost": "2"},
        ])
        self.assertEqual(self.client.post("/api/inventory/opening-stock/", duplicate, format="json").status_code, 400)
        for quantity in ("0", "-1", "not-a-number", "NaN", "1.0000000000001"):
            invalid = self._payload([{ "ingredient_id": self.item.pk, "quantity": quantity, "unit": "kg", "unit_cost": "2" }])
            self.assertEqual(self.client.post("/api/inventory/opening-stock/", invalid, format="json").status_code, 400, quantity)
        missing_cost = self._payload([{ "ingredient_id": self.item.pk, "quantity": "1", "unit": "kg" }])
        self.assertEqual(self.client.post("/api/inventory/opening-stock/", missing_cost, format="json").status_code, 400)
        negative_cost = self._payload([{ "ingredient_id": self.item.pk, "quantity": "1", "unit": "kg", "unit_cost": "-1" }])
        self.assertEqual(self.client.post("/api/inventory/opening-stock/", negative_cost, format="json").status_code, 400)
        incompatible = self._payload([{ "ingredient_id": self.item.pk, "quantity": "1", "unit": "pc", "unit_cost": "2" }])
        self.assertEqual(self.client.post("/api/inventory/opening-stock/", incompatible, format="json").status_code, 400)
        self.assertFalse(InventoryOperation.objects.exists())
        self.assertFalse(InventoryV1StockMovement.objects.exists())

    def test_business_scoping_permission_and_one_time_policy(self):
        foreign_warehouse = self.client.post("/api/inventory/opening-stock/", self._payload(warehouse_id=self.foreign_warehouse.pk), format="json")
        self.assertEqual(foreign_warehouse.status_code, 404)
        foreign_item = self.client.post("/api/inventory/opening-stock/", self._payload([
            {"ingredient_id": self.foreign_item.pk, "quantity": "1", "unit": "kg", "unit_cost": "2"}
        ]), format="json")
        self.assertEqual(foreign_item.status_code, 404)
        self.client.force_authenticate(self.viewer)
        denied = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(denied.status_code, 403)
        self.client.force_authenticate(self.owner)
        first = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(first.status_code, 201, first.data)
        repeated = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(repeated.status_code, 409, repeated.data)
        self.assertEqual(InventoryV1StockMovement.objects.filter(movement_type="opening_balance").count(), 1)

    def test_invalid_later_line_rolls_back_document_and_first_line(self):
        response = self.client.post("/api/inventory/opening-stock/", self._payload([
            {"ingredient_id": self.item.pk, "quantity": "2", "unit": "kg", "unit_cost": "4"},
            {"ingredient_id": self.inactive_item.pk, "quantity": "2", "unit": "pc", "unit_cost": "0"},
        ]), format="json")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(InventoryOperation.objects.exists())
        self.assertFalse(InventoryV1StockMovement.objects.exists())
        self.assertFalse(InventoryV1Stock.objects.exists())

    def test_opening_rejects_existing_projection_even_without_ledger(self):
        InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.item,
            unit="kg", quantity=Decimal("3"), average_cost=Decimal("1"),
        )
        response = self.client.post("/api/inventory/opening-stock/", self._payload(), format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(InventoryV1Stock.objects.get(ingredient=self.item).quantity, Decimal("3"))
        self.assertFalse(InventoryV1StockMovement.objects.exists())
