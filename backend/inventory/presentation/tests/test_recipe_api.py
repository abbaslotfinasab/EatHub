from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from core.enums import PermissionCode
from inventory.infrastructure.django.models import InventoryV1StockMovement
from inventory.models import Ingredient, Recipe, RecipeInput, RecipeOutput


class RecipeAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Recipe Business")
        self.other_business = Business.objects.create(name="Other Recipe Business")
        self.view_permission = Permission.objects.get_or_create(
            code=PermissionCode.INVENTORY_VIEW.value,
            defaults={"name": PermissionCode.INVENTORY_VIEW.label},
        )[0]
        self.manage_permission = Permission.objects.get_or_create(
            code=PermissionCode.INVENTORY_RECIPE_MANAGE.value,
            defaults={"name": PermissionCode.INVENTORY_RECIPE_MANAGE.label},
        )[0]
        self.owner = self._member(
            self.business, "recipe-owner", (self.view_permission, self.manage_permission)
        )
        self.viewer = self._member(self.business, "recipe-viewer", (self.view_permission,), "VIEWER")
        self.other_owner = self._member(
            self.other_business, "other-recipe-owner", (self.view_permission, self.manage_permission)
        )
        self.flour = Ingredient.objects.create(
            business=self.business, name="Flour", unit="kg", preparation_level="raw"
        )
        self.water = Ingredient.objects.create(
            business=self.business, name="Water", unit="l", preparation_level="raw"
        )
        self.inactive = Ingredient.objects.create(
            business=self.business, name="Inactive", unit="kg", is_active=False
        )
        self.foreign_ingredient = Ingredient.objects.create(
            business=self.other_business, name="Foreign Flour", unit="kg"
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
            email=f"{suffix}@example.test", password="not-used-in-test",
            name=suffix, number=f"93{len(suffix)}{business.pk}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def _payload(self, **changes):
        return {
            "name": "Pizza dough",
            "type": "preparation",
            "description": "Base dough",
            "inputs": [
                {"ingredient_id": self.flour.pk, "quantity": "500", "unit": "g"},
                {"ingredient_id": self.water.pk, "quantity": "250", "unit": "ml"},
            ],
            "outputs": [
                {"ingredient_id": self.flour.pk, "quantity": "0.7", "unit": "kg", "is_primary": True},
            ],
            **changes,
        }

    def _create_recipe(self, **changes):
        response = self.client.post(
            "/api/inventory/recipes/", self._payload(**changes), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response

    def test_recipe_crud_and_input_output_line_management(self):
        created = self._create_recipe(
            code="DOUGH",
            inputs=[
                {"ingredient_id": self.flour.pk, "quantity": "500", "unit": "g"},
            ],
        )
        recipe_id = created.data["id"]
        self.assertEqual(created.data["inputs"][0]["quantity"], "0.500000000000")
        self.assertEqual(created.data["inputs"][0]["unit"], "kg")
        self.assertTrue(created.data["outputs"][0]["is_primary"])

        listed = self.client.get("/api/inventory/recipes/?search=dough&type=preparation")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(listed.data["results"][0]["id"], recipe_id)
        self.assertEqual(self.client.get(f"/api/inventory/recipes/{recipe_id}/").status_code, 200)

        updated = self.client.patch(
            f"/api/inventory/recipes/{recipe_id}/",
            {"description": "Updated", "is_active": False}, format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["is_active"])

        added = self.client.post(
            f"/api/inventory/recipes/{recipe_id}/inputs/",
            {"ingredient_id": self.water.pk, "quantity": "1", "unit": "l"}, format="json",
        )
        self.assertEqual(added.status_code, 201)
        input_id = next(row["id"] for row in added.data["inputs"] if row["quantity"] == "1.000000000000")
        patched = self.client.patch(
            f"/api/inventory/recipes/{recipe_id}/inputs/{input_id}/",
            {"quantity": "2"}, format="json",
        )
        self.assertEqual(patched.status_code, 200)
        self.assertTrue(any(row["id"] == input_id and row["quantity"] == "2.000000000000" for row in patched.data["inputs"]))

        added_output = self.client.post(
            f"/api/inventory/recipes/{recipe_id}/outputs/",
            {"ingredient_id": self.water.pk, "quantity": "1", "unit": "l"}, format="json",
        )
        self.assertEqual(added_output.status_code, 201)
        output_id = next(row["id"] for row in added_output.data["outputs"] if row["ingredient_id"] == self.water.pk)
        patched_output = self.client.patch(
            f"/api/inventory/recipes/{recipe_id}/outputs/{output_id}/",
            {"is_primary": False}, format="json",
        )
        self.assertEqual(patched_output.status_code, 200)
        self.assertEqual(
            self.client.delete(f"/api/inventory/recipes/{recipe_id}/outputs/{output_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            self.client.delete(f"/api/inventory/recipes/{recipe_id}/inputs/{input_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(InventoryV1StockMovement.objects.exists())

    def test_authentication_and_write_permission_are_enforced(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/inventory/recipes/").status_code, 401)
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get("/api/inventory/recipes/").status_code, 200)
        self.assertEqual(self.client.post("/api/inventory/recipes/", self._payload(), format="json").status_code, 403)
        self.assertEqual(self.client.patch("/api/inventory/recipes/1/", {"name": "Denied"}, format="json").status_code, 403)

    def test_recipe_and_line_resources_are_business_scoped(self):
        foreign = Recipe.objects.create(business=self.other_business, name="Private")
        self.assertEqual(self.client.get(f"/api/inventory/recipes/{foreign.pk}/").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/inventory/recipes/{foreign.pk}/", {"name": "Changed"}, format="json").status_code, 404)
        response = self.client.get("/api/inventory/recipes/?search=Private")
        self.assertEqual(response.data["count"], 0)
        bad = self.client.post(
            "/api/inventory/recipes/",
            self._payload(inputs=[{"ingredient_id": self.foreign_ingredient.pk, "quantity": "1", "unit": "kg"}]),
            format="json",
        )
        self.assertEqual(bad.status_code, 404)
        self.assertFalse(Recipe.objects.filter(business=self.business).exists())

    def test_duplicate_inactive_invalid_and_incompatible_lines_are_rejected_atomically(self):
        cases = [
            ([{"ingredient_id": self.flour.pk, "quantity": "0", "unit": "kg"}], 400),
            ([{"ingredient_id": self.flour.pk, "quantity": "-1", "unit": "kg"}], 400),
            ([{"ingredient_id": self.flour.pk, "quantity": "1e100", "unit": "kg"}], 400),
            ([{"ingredient_id": self.flour.pk, "quantity": "1.0000000000001", "unit": "kg"}], 400),
            ([{"ingredient_id": self.inactive.pk, "quantity": "1", "unit": "kg"}], 400),
            ([{"ingredient_id": self.flour.pk, "quantity": "1", "unit": "l"}], 400),
            ([
                {"ingredient_id": self.flour.pk, "quantity": "1", "unit": "kg"},
                {"ingredient_id": self.flour.pk, "quantity": "2", "unit": "kg"},
            ], 400),
        ]
        for inputs, expected in cases:
            with self.subTest(inputs=inputs):
                response = self.client.post(
                    "/api/inventory/recipes/", self._payload(inputs=inputs), format="json"
                )
                self.assertEqual(response.status_code, expected)
                self.assertFalse(Recipe.objects.filter(business=self.business).exists())

        valid_then_invalid = self.client.post(
            "/api/inventory/recipes/",
            self._payload(inputs=[
                {"ingredient_id": self.flour.pk, "quantity": "1", "unit": "kg"},
                {"ingredient_id": self.inactive.pk, "quantity": "1", "unit": "kg"},
            ]),
            format="json",
        )
        self.assertEqual(valid_then_invalid.status_code, 400)
        self.assertFalse(Recipe.objects.filter(business=self.business).exists())
        self.assertFalse(RecipeInput.objects.exists())
        self.assertFalse(RecipeOutput.objects.exists())

    def test_line_unit_remains_stable_after_ingredient_unit_change(self):
        created = self._create_recipe(inputs=[
            {"ingredient_id": self.flour.pk, "quantity": "0.25", "unit": "kg"},
        ], outputs=[])
        self.flour.unit = "g"
        self.flour.save(update_fields=("unit",))
        detail = self.client.get(f"/api/inventory/recipes/{created.data['id']}/")
        self.assertEqual(detail.data["inputs"][0]["unit"], "kg")
        self.assertEqual(detail.data["inputs"][0]["quantity"], "0.250000000000")

    def test_pagination_filtering_and_search(self):
        self._create_recipe(name="A dough")
        self._create_recipe(name="B dough")
        self._create_recipe(name="C sauce", type="production")
        page = self.client.get("/api/inventory/recipes/?page=2&page_size=1&search=dough")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.data["count"], 2)
        self.assertEqual(page.data["page"], 2)
        inactive = self.client.get("/api/inventory/recipes/?is_active=false")
        self.assertEqual(inactive.data["count"], 0)

