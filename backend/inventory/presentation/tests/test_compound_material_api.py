from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import InventoryV1StockMovement
from inventory.models import Ingredient, RecipeInput


class CompoundMaterialAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Compound Material Business")
        self.other_business = Business.objects.create(name="Other Compound Material Business")
        self.view = self._permission(PermissionCode.INVENTORY_VIEW)
        self.manage = self._permission(PermissionCode.INVENTORY_COMPOUND_MANAGE)
        self.adjust = self._permission(PermissionCode.INVENTORY_ADJUST)
        self.warehouse_manage = self._permission(PermissionCode.INVENTORY_WAREHOUSE_MANAGE)
        self.item_manage = self._permission(PermissionCode.INVENTORY_ITEM_MANAGE)
        self.recipe_manage = self._permission(PermissionCode.INVENTORY_RECIPE_MANAGE)
        self.owner = self._member(self.business, "compound-owner", (self.view, self.manage, self.adjust, self.warehouse_manage, self.item_manage, self.recipe_manage))
        self.viewer = self._member(self.business, "compound-viewer", (self.view,), "VIEWER")
        self.other_owner = self._member(self.other_business, "other-compound-owner", (self.view, self.manage, self.adjust))
        self.tomato = Ingredient.objects.create(business=self.business, name="Tomato", unit="kg", preparation_level="raw")
        self.onion = Ingredient.objects.create(business=self.business, name="Onion", unit="kg", preparation_level="raw")
        self.inactive = Ingredient.objects.create(business=self.business, name="Inactive", unit="kg", preparation_level="raw", is_active=False)
        self.foreign = Ingredient.objects.create(business=self.other_business, name="Foreign", unit="kg", preparation_level="raw")
        self.client.force_authenticate(self.owner)

    @staticmethod
    def _permission(code):
        return Permission.objects.get_or_create(code=code.value, defaults={"name": code.label})[0]

    @staticmethod
    def _member(business, email, permissions, code="OWNER"):
        role = Role.objects.create(business=business, name=code.title(), code=code, is_system=True)
        for permission in permissions:
            RolePermission.objects.get_or_create(role=role, permission=permission)
        user = User.objects.create_user(email=f"{email}@example.test", password="not-used", name=email, number=f"95{business.pk}{len(email)}")
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def _payload(self, **changes):
        return {
            "name": "House sauce", "sku": "SAUCE", "unit": "kg",
            "components": [
                {"ingredient_id": self.tomato.pk, "quantity": "0.5", "unit": "kg"},
                {"ingredient_id": self.onion.pk, "quantity": "100", "unit": "g"},
            ],
            **changes,
        }

    def test_create_list_detail_patch_and_deactivate_preserve_composition_and_stock_ledger(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED, created.data)
        compound_id = created.data["id"]
        compound = Ingredient.objects.get(pk=compound_id)
        self.assertEqual(compound.preparation_level, Ingredient.PreparationLevel.SEMI_PREPARED)
        self.assertEqual(len(created.data["components"]), 2)
        self.assertEqual(created.data["components"][1]["quantity"], "100.000000000000")
        listed = self.client.get("/api/inventory/compound-materials/?search=sauce")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual([row["id"] for row in listed.data["results"]], [compound_id])
        self.assertEqual(self.client.get(f"/api/inventory/compound-materials/{compound_id}/").status_code, 200)
        updated = self.client.patch(f"/api/inventory/compound-materials/{compound_id}/", {"name": "Tomato sauce"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(len(updated.data["components"]), 2)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)
        self.assertEqual(self.client.patch(f"/api/inventory/compound-materials/{compound_id}/", {"is_active": False}, format="json").status_code, 200)

    def test_composition_rejects_short_duplicate_invalid_inactive_and_foreign_components(self):
        cases = [
            ([{"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "kg"}] * 2, "components"),
            ([{"ingredient_id": self.tomato.pk, "quantity": "0", "unit": "kg"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.tomato.pk, "quantity": "0.0000000000001", "unit": "kg"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "l"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.inactive.pk, "quantity": "1", "unit": "kg"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.foreign.pk, "quantity": "1", "unit": "kg"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "kg"}, {"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "kg"}], "components"),
            ([{"ingredient_id": 999999, "quantity": "1", "unit": "kg"}, {"ingredient_id": self.onion.pk, "quantity": "1", "unit": "kg"}], "components"),
        ]
        for components, _field in cases:
            with self.subTest(components=components):
                response = self.client.post("/api/inventory/compound-materials/", self._payload(components=components), format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(Ingredient.objects.filter(preparation_level="semi_prepared").count(), 0)

    def test_invalid_composition_update_preserves_existing_lines_atomically(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        before = self.client.get(f"/api/inventory/compound-materials/{created.data['id']}/").data["components"]
        response = self.client.patch(f"/api/inventory/compound-materials/{created.data['id']}/", {
            "name": "Should roll back", "components": [
                {"ingredient_id": self.tomato.pk, "quantity": "1", "unit": "kg"},
                {"ingredient_id": self.foreign.pk, "quantity": "1", "unit": "kg"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        after = self.client.get(f"/api/inventory/compound-materials/{created.data['id']}/").data
        self.assertEqual(after["name"], "House sauce")
        self.assertEqual(after["components"], before)

    def test_permissions_and_tenant_scoping(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        foreign = Ingredient.objects.create(
            business=self.other_business,
            name="Other business compound",
            unit="kg",
            preparation_level="semi_prepared",
        )
        listed = self.client.get("/api/inventory/compound-materials/")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listed.data["results"]], [created.data["id"]])

        no_viewer = self._member(self.business, "compound-no-view", (), "NO_INVENTORY_ACCESS")
        self.client.force_authenticate(no_viewer)
        self.assertEqual(self.client.get("/api/inventory/compound-materials/").status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/inventory/compound-materials/").status_code, 200)
        self.assertEqual(self.client.post("/api/inventory/compound-materials/", self._payload(name="Denied", sku="DENIED"), format="json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/inventory/compound-materials/{created.data['id']}/", {"name": "Denied"}, format="json").status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(f"/api/inventory/compound-materials/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/inventory/compound-materials/{foreign.pk}/", {"name": "Leak"}, format="json").status_code, 404)

    def test_compound_material_is_a_recipe_ingredient_without_automatic_consumption(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        compound_id = created.data["id"]
        recipe = self.client.post("/api/inventory/recipes/", {
            "name": "Sauce bowl", "inputs": [{"ingredient_id": compound_id, "quantity": "50", "unit": "g"}],
            "outputs": [{"ingredient_id": compound_id, "quantity": "0.25", "unit": "kg", "is_primary": True}],
        }, format="json")
        self.assertEqual(recipe.status_code, status.HTTP_201_CREATED, recipe.data)
        self.assertEqual(recipe.data["inputs"][0]["material_type"], "compound")
        self.assertEqual(recipe.data["outputs"][0]["material_type"], "compound")
        self.assertEqual(RecipeInput.objects.filter(recipe_id=recipe.data["id"], ingredient_id=compound_id).count(), 1)
        unit_change = self.client.patch(f"/api/inventory/compound-materials/{compound_id}/", {"unit": "g"}, format="json")
        self.assertEqual(unit_change.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_compounds_participate_in_balances_and_opening_stock(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        empty_compound_balances = self.client.get("/api/inventory/balances/?material_type=compound")
        self.assertEqual(empty_compound_balances.status_code, status.HTTP_200_OK)
        self.assertEqual(empty_compound_balances.data["count"], 0)

        warehouse = self.client.post("/api/inventory/warehouses/", {"name": "Main"}, format="json")
        opening = self.client.post("/api/inventory/opening-stock/", {
            "warehouse_id": warehouse.data["id"], "lines": [
                {"ingredient_id": created.data["id"], "material_type": "compound", "quantity": "2", "unit": "kg", "unit_cost": "4.25"},
                {"ingredient_id": self.tomato.pk, "material_type": "raw", "quantity": "3", "unit": "kg", "unit_cost": "2.00"},
            ],
        }, format="json")
        self.assertEqual(opening.status_code, status.HTTP_201_CREATED, opening.data)
        balances = self.client.get("/api/inventory/balances/?material_type=compound")
        self.assertEqual(balances.status_code, 200)
        self.assertEqual(balances.data["results"][0]["material_type"], "compound")
        self.assertEqual(Decimal(balances.data["results"][0]["quantity"]), Decimal("2"))
        all_balances = self.client.get("/api/inventory/balances/?warehouse_id=" + str(warehouse.data["id"]))
        self.assertEqual(all_balances.status_code, status.HTTP_200_OK)
        self.assertEqual(all_balances.data["count"], 2)
        self.assertEqual(
            {row["ingredient_id"]: row["material_type"] for row in all_balances.data["results"]},
            {created.data["id"]: "compound", self.tomato.pk: "raw"},
        )
        issue = self.client.post("/api/inventory/issues/", {
            "warehouse_id": warehouse.data["id"], "reason": "Preparation use",
            "lines": [{"ingredient_id": created.data["id"], "material_type": "compound", "quantity": "0.5", "unit": "kg"}],
        }, format="json")
        self.assertEqual(issue.status_code, status.HTTP_201_CREATED, issue.data)
        posted = self.client.post(f"/api/inventory/issues/{issue.data['id']}/post/", {}, format="json")
        self.assertEqual(posted.status_code, status.HTTP_200_OK, posted.data)
        self.assertEqual(posted.data["lines"][0]["material_type"], "compound")
        movement = self.client.get("/api/inventory/movements/?material_type=compound")
        self.assertEqual(movement.status_code, status.HTTP_200_OK)
        self.assertTrue(all(row["material_type"] == "compound" for row in movement.data["results"]))

    def test_opening_entry_rejects_a_material_type_that_disagrees_with_the_item(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        warehouse = self.client.post("/api/inventory/warehouses/", {"name": "Type Check Warehouse"}, format="json")
        response = self.client.post("/api/inventory/opening-stock/", {
            "warehouse_id": warehouse.data["id"], "lines": [{
                "ingredient_id": created.data["id"], "material_type": "raw", "quantity": "1", "unit": "kg", "unit_cost": "0",
            }],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

    def test_raw_ingredients_used_in_compounds_cannot_be_deactivated(self):
        created = self.client.post("/api/inventory/compound-materials/", self._payload(), format="json")
        response = self.client.patch(f"/api/inventory/items/{self.tomato.pk}/", {"is_active": False}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Ingredient.objects.get(pk=self.tomato.pk).is_active)
