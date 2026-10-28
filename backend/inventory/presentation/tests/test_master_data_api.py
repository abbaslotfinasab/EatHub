from django.db import IntegrityError, transaction
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.master_data_repository import DjangoMasterDataRepository
from inventory.models import Ingredient, Warehouse


class InventoryMasterDataAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Master Data Business")
        self.other_business = Business.objects.create(name="Other Master Data Business")
        self.view_permission = Permission.objects.create(
            code=PermissionCode.INVENTORY_VIEW.value,
            name=PermissionCode.INVENTORY_VIEW.label,
        )
        self.item_manage, _ = Permission.objects.get_or_create(
            code=PermissionCode.INVENTORY_ITEM_MANAGE.value,
            defaults={"name": PermissionCode.INVENTORY_ITEM_MANAGE.label},
        )
        self.warehouse_manage, _ = Permission.objects.get_or_create(
            code=PermissionCode.INVENTORY_WAREHOUSE_MANAGE.value,
            defaults={"name": PermissionCode.INVENTORY_WAREHOUSE_MANAGE.label},
        )
        self.owner = self._member(self.business, "owner", (self.view_permission, self.item_manage, self.warehouse_manage))
        self.manager = self._member(self.business, "manager", (self.view_permission, self.item_manage, self.warehouse_manage), code="MANAGER")
        self.viewer = self._member(self.business, "viewer", (self.view_permission,), code="VIEWER")
        self.other_owner = self._member(self.other_business, "other", (self.view_permission, self.item_manage, self.warehouse_manage))
        self.no_membership = User.objects.create_user(
            email="no-membership@example.test", password="not-used-in-test",
            name="No membership", number="919999",
        )
        self.client.force_authenticate(self.owner)

    @staticmethod
    def _member(business, suffix, permissions, code="OWNER"):
        role = Role.objects.create(
            business=business, name=code.title(), code=code, is_system=True
        )
        for permission in permissions:
            RolePermission.objects.get_or_create(role=role, permission=permission)
        user = User.objects.create_user(
            email=f"{suffix}@example.test",
            password="not-used-in-test",
            name=suffix,
            number=f"91{len(suffix)}{business.pk}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def test_item_list_create_detail_and_patch_use_the_business_scope(self):
        response = self.client.post("/api/inventory/items/", {
            "name": "Flour", "sku": "  FLOUR-1  ", "unit": "kg",
            "preparation_level": "raw", "is_active": True,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item_id = response.data["id"]
        self.assertEqual(response.data["sku"], "FLOUR-1")
        self.assertEqual(response.data["unit"], "kg")
        self.assertNotIn("business_id", response.data)
        self.assertTrue(
            Ingredient.objects.filter(pk=item_id, business=self.business).exists()
        )
        blank_sku = self.client.post(
            "/api/inventory/items/",
            {"name": "Water", "sku": "   ", "unit": "l"},
            format="json",
        )
        self.assertEqual(blank_sku.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(blank_sku.data["sku"])

        direct_count, _ = DjangoMasterDataRepository.list_items(
            self.business.id, page=1, page_size=10, search="flour"
        )
        self.assertEqual(direct_count, 1)
        listing = self.client.get("/api/inventory/items/?page=1&page_size=10&search=flour")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], item_id)
        self.assertEqual(self.client.get(f"/api/inventory/items/{item_id}/").status_code, status.HTTP_200_OK)
        updated = self.client.patch(f"/api/inventory/items/{item_id}/", {"is_active": False}, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertFalse(updated.data["is_active"])

    def test_authentication_and_active_membership_are_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/inventory/items/").status_code, 401)
        self.client.force_authenticate(self.no_membership)
        self.assertEqual(self.client.get("/api/inventory/warehouses/").status_code, 403)

    def test_item_sku_unique_per_business_and_stock_fields_are_rejected(self):
        payload = {"name": "Salt", "sku": "SALT", "unit": "kg"}
        self.assertEqual(self.client.post("/api/inventory/items/", payload, format="json").status_code, 201)
        duplicate = self.client.post("/api/inventory/items/", {**payload, "name": "Fine salt"}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        case_variant = self.client.post(
            "/api/inventory/items/",
            {"name": "Sea Salt", "sku": "salt", "unit": "kg"},
            format="json",
        )
        self.assertEqual(case_variant.status_code, status.HTTP_201_CREATED)
        foreign = self.client.post("/api/inventory/items/", {**payload, "name": "Salt", "business_id": self.other_business.pk}, format="json")
        self.assertEqual(foreign.status_code, status.HTTP_400_BAD_REQUEST)
        for unsupported in ({"current_stock": 10}, {"average_cost": "3.00"}, {"cost_price": "3.00"}):
            with self.subTest(unsupported=unsupported):
                stock_field = self.client.post(
                    "/api/inventory/items/",
                    {"name": "Rice", "unit": "kg", **unsupported},
                    format="json",
                )
                self.assertEqual(stock_field.status_code, status.HTTP_400_BAD_REQUEST)

        compound_bypass = self.client.post(
            "/api/inventory/items/",
            {"name": "Compound bypass", "unit": "kg", "preparation_level": "semi_prepared"},
            format="json",
        )
        self.assertEqual(compound_bypass.status_code, status.HTTP_400_BAD_REQUEST)

        referenced = Ingredient.objects.create(business=self.business, name="Referenced Flour", unit="kg")
        from inventory.infrastructure.django.models import InventoryV1Stock
        InventoryV1Stock.objects.create(
            business=self.business, warehouse=Warehouse.objects.create(business=self.business, name="Unit Lock Warehouse"),
            ingredient=referenced, unit="kg", quantity=0, average_cost=0,
        )
        locked_unit = self.client.patch(
            f"/api/inventory/items/{referenced.pk}/", {"unit": "g"}, format="json"
        )
        self.assertEqual(locked_unit.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(self.other_owner)
        same_sku_other_business = self.client.post("/api/inventory/items/", payload, format="json")
        self.assertEqual(same_sku_other_business.status_code, status.HTTP_201_CREATED)

    def test_database_enforces_business_scoped_sku_uniqueness(self):
        Ingredient.objects.create(business=self.business, name="DB item 1", unit="kg", sku="DB-SKU")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Ingredient.objects.create(business=self.business, name="DB item 2", unit="kg", sku="DB-SKU")

    def test_item_tenant_detail_and_update_hide_foreign_rows(self):
        foreign = Ingredient.objects.create(
            business=self.other_business, name="Foreign", unit="kg", sku="F-1"
        )
        self.assertEqual(self.client.get(f"/api/inventory/items/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/inventory/items/{foreign.pk}/", {"name": "Changed"}, format="json").status_code, 404)
        self.assertEqual(self.client.get("/api/inventory/items/?search=Foreign").data["count"], 0)
        foreign_warehouse = Warehouse.objects.create(
            business=self.other_business, name="Foreign warehouse"
        )
        self.assertEqual(self.client.get(f"/api/inventory/warehouses/{foreign_warehouse.pk}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/inventory/warehouses/{foreign_warehouse.pk}/", {"name": "Changed"}, format="json").status_code, 404)

    def test_management_permissions_are_separate_from_view_and_adjust(self):
        self.client.force_authenticate(self.viewer)
        with patch(
            "inventory.presentation.master_data_views.DjangoMasterDataRepository.list_items",
            return_value=(0, []),
        ) as list_items:
            self.assertEqual(self.client.get("/api/inventory/items/").status_code, 200)
        list_items.assert_called_once()
        self.assertEqual(self.client.post("/api/inventory/items/", {"name": "Denied", "unit": "kg"}, format="json").status_code, 403)
        self.assertEqual(self.client.post("/api/inventory/warehouses/", {"name": "Denied"}, format="json").status_code, 403)

        with patch("inventory.presentation.master_data_views.DjangoMasterDataRepository.save_item") as save_item:
            self.assertEqual(self.client.post("/api/inventory/items/", {"name": "Denied", "unit": "kg"}, format="json").status_code, 403)
        save_item.assert_not_called()
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get("/api/inventory/items/").status_code, 200)
        self.assertEqual(self.client.get("/api/inventory/warehouses/").status_code, 200)
        self.assertEqual(self.client.post("/api/inventory/items/", {"name": "Manager item", "unit": "pc"}, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/inventory/warehouses/", {"name": "Manager warehouse"}, format="json").status_code, 201)

    def test_warehouse_default_reassignment_and_business_isolation(self):
        first = self.client.post("/api/inventory/warehouses/", {"name": "Main", "is_default": True}, format="json")
        second = self.client.post("/api/inventory/warehouses/", {"name": "Backup", "is_default": True}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertFalse(Warehouse.objects.get(pk=first.data["id"]).is_default)
        self.assertTrue(Warehouse.objects.get(pk=second.data["id"]).is_default)

        self.client.force_authenticate(self.other_owner)
        other_default = self.client.post("/api/inventory/warehouses/", {"name": "Other Main", "is_default": True}, format="json")
        self.assertEqual(other_default.status_code, 201)
        self.assertTrue(
            Warehouse.objects.filter(pk=other_default.data["id"], business=self.other_business).exists()
        )
        direct_count, _ = DjangoMasterDataRepository.list_warehouses(
            self.other_business.id, page=1, page_size=20
        )
        self.assertEqual(direct_count, 1)
        listing = self.client.get("/api/inventory/warehouses/")
        self.assertEqual(listing.data["count"], 1)

        self.client.force_authenticate(self.owner)
        disabled = self.client.patch(f"/api/inventory/warehouses/{second.data['id']}/", {"is_active": False}, format="json")
        self.assertEqual(disabled.status_code, 200)
        self.assertFalse(disabled.data["is_default"])

    def test_warehouse_query_and_payload_validation(self):
        response = self.client.post("/api/inventory/warehouses/", {"name": "North", "code": "N"}, format="json")
        self.assertEqual(response.status_code, 201)
        invalid = self.client.post("/api/inventory/warehouses/", {"name": "Disabled", "is_default": True, "is_active": False}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.client.get("/api/inventory/warehouses/?is_active=true&search=north").data["count"], 1)
        self.assertEqual(self.client.get("/api/inventory/warehouses/?page_size=101").status_code, 400)
        self.assertEqual(self.client.post("/api/inventory/warehouses/", {"name": "Forged", "actor_id": 4}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(f"/api/inventory/warehouses/{response.data['id']}/").status_code, 405)

    def test_database_allows_only_one_active_default_per_business(self):
        Warehouse.objects.create(business=self.business, name="DB default 1", is_default=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.create(business=self.business, name="DB default 2", is_default=True)
