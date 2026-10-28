from decimal import Decimal
from uuid import uuid4

from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import InventoryReservation, InventoryV1Stock, InventoryV1StockMovement
from inventory.models import Ingredient, Warehouse


class InventoryReservationsAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Reservation business")
        self.other_business = Business.objects.create(name="Other reservation business")
        self.view_permission = Permission.objects.create(code=PermissionCode.INVENTORY_VIEW.value, name="View Inventory")
        self.adjust_permission = Permission.objects.create(code=PermissionCode.INVENTORY_ADJUST.value, name="Adjust Inventory")
        self.owner = self._member(self.business, "reservation-owner", (self.view_permission, self.adjust_permission), "OWNER")
        self.viewer = self._member(self.business, "reservation-viewer", (self.view_permission,), "VIEWER")
        self.other_owner = self._member(self.other_business, "reservation-other", (self.view_permission, self.adjust_permission), "OWNER")
        self.warehouse = Warehouse.objects.create(business=self.business, name="Main")
        self.other_warehouse = Warehouse.objects.create(business=self.other_business, name="Foreign")
        self.rice = Ingredient.objects.create(business=self.business, name="Rice", unit="kg")
        self.beans = Ingredient.objects.create(business=self.business, name="Beans", unit="kg")
        self.foreign_item = Ingredient.objects.create(business=self.other_business, name="Foreign item", unit="kg")
        self.rice_stock = InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.rice,
            unit="kg", quantity=Decimal("10"), average_cost=Decimal("2"),
        )
        InventoryV1Stock.objects.create(
            business=self.business, warehouse=self.warehouse, ingredient=self.beans,
            unit="kg", quantity=Decimal("1"), average_cost=Decimal("3"),
        )
        self.client.force_authenticate(self.owner)

    @staticmethod
    def _member(business, suffix, permissions, role_code):
        role = Role.objects.create(business=business, name=role_code, code=f"{role_code}-{suffix}")
        for permission in permissions:
            RolePermission.objects.create(role=role, permission=permission)
        user = User.objects.create_user(
            email=f"{suffix}@example.test", password="unused-test-password",
            name=suffix, number=f"res-{suffix}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def _payload(self, *, lines=None, key=None, warehouse_id=None):
        return {
            "warehouse_id": warehouse_id or self.warehouse.pk,
            "source_type": "manual",
            "reason": "Reservation for confirmed work",
            "idempotency_key": str(key or uuid4()),
            "lines": lines or [{"ingredient_id": self.rice.pk, "quantity": "3", "unit": "kg"}],
        }

    def test_single_reservation_changes_availability_not_physical_stock_or_ledger(self):
        response = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.rice_stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)
        availability = self.client.get(
            f"/api/inventory/reservations/availability/?warehouse_id={self.warehouse.pk}&ingredient_id={self.rice.pk}"
        )
        self.assertEqual(availability.status_code, 200, availability.data)
        self.assertEqual(availability.data["physical_quantity"], "10.000000000000")
        self.assertEqual(availability.data["reserved_quantity"], "3.000000000000")
        self.assertEqual(availability.data["available_quantity"], "7.000000000000")

    def test_multi_line_reservation_is_all_or_nothing(self):
        response = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.rice.pk, "quantity": "2", "unit": "kg"},
            {"ingredient_id": self.beans.pk, "quantity": "2", "unit": "kg"},
        ]), format="json")
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(InventoryReservation.objects.count(), 0)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.rice_stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_duplicate_manual_ingredient_lines_are_rejected(self):
        response = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.rice.pk, "quantity": "1", "unit": "kg"},
            {"ingredient_id": self.rice.pk, "quantity": "1", "unit": "kg"},
        ]), format="json")
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(InventoryReservation.objects.count(), 0)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.rice_stock.pk).quantity, Decimal("10"))

    def test_manual_source_policy_rejects_external_sources_and_identifiers(self):
        unsupported_payload = self._payload()
        unsupported_payload["source_type"] = "order"
        unsupported = self.client.post(
            "/api/inventory/reservations/", unsupported_payload, format="json"
        )
        self.assertEqual(unsupported.status_code, 400, unsupported.data)
        source_id = self._payload()
        source_id["source_id"] = 5
        self.assertEqual(
            self.client.post("/api/inventory/reservations/", source_id, format="json").status_code,
            400,
        )
        source_line = self._payload(lines=[{
            "ingredient_id": self.rice.pk, "source_line_id": 5,
            "quantity": "1", "unit": "kg",
        }])
        self.assertEqual(
            self.client.post("/api/inventory/reservations/", source_line, format="json").status_code,
            400,
        )
        self.assertEqual(InventoryReservation.objects.count(), 0)

    def test_issue_cannot_reduce_physical_stock_below_active_reservations(self):
        reserved = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.rice.pk, "quantity": "8", "unit": "kg"},
        ]), format="json")
        self.assertEqual(reserved.status_code, 201, reserved.data)
        issue = self.client.post("/api/inventory/issues/", {
            "warehouse_id": self.warehouse.pk,
            "reason": "Kitchen use",
            "lines": [{"ingredient_id": self.rice.pk, "quantity": "3", "unit": "kg"}],
        }, format="json")
        self.assertEqual(issue.status_code, 201, issue.data)
        posted = self.client.post(f"/api/inventory/issues/{issue.data['id']}/post/", {}, format="json")
        self.assertEqual(posted.status_code, 409, posted.data)
        self.assertEqual(InventoryV1Stock.objects.get(pk=self.rice_stock.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)
        availability = self.client.get(
            f"/api/inventory/reservations/availability/?warehouse_id={self.warehouse.pk}&ingredient_id={self.rice.pk}"
        )
        self.assertEqual(availability.data["available_quantity"], "2.000000000000")

    def test_unit_conversion_and_replay_are_idempotent(self):
        key = uuid4()
        payload = self._payload(key=key, lines=[{"ingredient_id": self.rice.pk, "quantity": "500", "unit": "g"}])
        first = self.client.post("/api/inventory/reservations/", payload, format="json")
        replay = self.client.post("/api/inventory/reservations/", payload, format="json")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(replay.status_code, 201, replay.data)
        self.assertEqual(first.data["id"], replay.data["id"])
        self.assertEqual(first.data["lines"][0]["quantity"], "0.500000000000")
        changed = self.client.post("/api/inventory/reservations/", self._payload(key=key, lines=[
            {"ingredient_id": self.rice.pk, "quantity": "600", "unit": "g"},
        ]), format="json")
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(InventoryReservation.objects.count(), 1)

    def test_release_is_idempotent_and_restores_availability_without_movement(self):
        created = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        key = str(uuid4())
        payload = {"idempotency_key": key, "reason": "Order cancelled before preparation"}
        first = self.client.post(f"/api/inventory/reservations/{created.data['id']}/release/", payload, format="json")
        replay = self.client.post(f"/api/inventory/reservations/{created.data['id']}/release/", payload, format="json")
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(first.data["status"], "released")
        availability = self.client.get(
            f"/api/inventory/reservations/availability/?warehouse_id={self.warehouse.pk}&ingredient_id={self.rice.pk}"
        )
        self.assertEqual(availability.data["reserved_quantity"], "0")
        self.assertEqual(availability.data["available_quantity"], "10.000000000000")
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_release_key_cannot_be_reused_for_another_reservation(self):
        first = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        second = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.beans.pk, "quantity": "1", "unit": "kg"},
        ]), format="json")
        key = str(uuid4())
        release_payload = {"idempotency_key": key, "reason": "Manual release"}
        released = self.client.post(f"/api/inventory/reservations/{first.data['id']}/release/", release_payload, format="json")
        conflict = self.client.post(f"/api/inventory/reservations/{second.data['id']}/release/", release_payload, format="json")
        self.assertEqual(released.status_code, 200, released.data)
        self.assertEqual(conflict.status_code, 409, conflict.data)

    def test_invalid_quantities_units_and_missing_stock_are_rejected(self):
        for quantity in ("0", "-1"):
            response = self.client.post("/api/inventory/reservations/", self._payload(lines=[
                {"ingredient_id": self.rice.pk, "quantity": quantity, "unit": "kg"},
            ]), format="json")
            self.assertEqual(response.status_code, 400)
        incompatible = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.rice.pk, "quantity": "1", "unit": "pc"},
        ]), format="json")
        self.assertEqual(incompatible.status_code, 400)
        missing_stock = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": self.foreign_item.pk, "quantity": "1", "unit": "kg"},
        ]), format="json")
        self.assertEqual(missing_stock.status_code, 404)
        no_position_item = Ingredient.objects.create(business=self.business, name="No stock", unit="kg")
        missing_position = self.client.post("/api/inventory/reservations/", self._payload(lines=[
            {"ingredient_id": no_position_item.pk, "quantity": "1", "unit": "kg"},
        ]), format="json")
        self.assertEqual(missing_position.status_code, 409)
        self.assertEqual(InventoryReservation.objects.count(), 0)

    def test_business_scope_and_permission_are_enforced(self):
        foreign_warehouse = self.client.post("/api/inventory/reservations/", self._payload(
            warehouse_id=self.other_warehouse.pk,
        ), format="json")
        self.assertEqual(foreign_warehouse.status_code, 404)
        created = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        self.client.force_authenticate(self.other_owner)
        self.assertEqual(self.client.get(f"/api/inventory/reservations/{created.data['id']}/").status_code, 404)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/inventory/reservations/").status_code, 200)
        denied = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        self.assertEqual(denied.status_code, 403)

    def test_list_and_detail_return_auditable_business_scoped_history(self):
        created = self.client.post("/api/inventory/reservations/", self._payload(), format="json")
        detail = self.client.get(f"/api/inventory/reservations/{created.data['id']}/")
        history = self.client.get("/api/inventory/reservations/?source_type=manual")
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertEqual(history.status_code, 200, history.data)
        self.assertEqual(history.data["count"], 1)
        self.assertEqual(detail.data["created_by_id"], self.owner.pk)
        self.assertEqual(detail.data["lines"][0]["ingredient_name"], "Rice")

    def test_database_rejects_unsupported_reservation_status(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryReservation.objects.create(
                    business=self.business,
                    warehouse=self.warehouse,
                    source_type="manual",
                    source_id=None,
                    reason="Invalid status constraint test",
                    status="cancelled",
                    idempotency_key=uuid4(),
                    payload_fingerprint="0" * 64,
                    created_by_id=self.owner.pk,
                )
