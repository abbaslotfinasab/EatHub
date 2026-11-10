from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from catalog.models import Product, ProductAllergen, ProductDietaryTag
from core.enums import PermissionCode


class ProductCatalogAPITests(APITestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Catalog Business")
        self.other_business = Business.objects.create(name="Other Catalog Business")
        self.view_permission = self._permission(PermissionCode.PRODUCTS_VIEW)
        self.create_permission = self._permission(PermissionCode.PRODUCTS_CREATE)
        self.update_permission = self._permission(PermissionCode.PRODUCTS_UPDATE)
        self.owner = self._member(self.business, "catalog-owner", (
            self.view_permission, self.create_permission, self.update_permission,
        ))
        self.viewer = self._member(self.business, "catalog-viewer", (self.view_permission,), code="VIEWER")
        self.other_owner = self._member(self.other_business, "catalog-other", (
            self.view_permission, self.create_permission, self.update_permission,
        ))
        self.client.force_authenticate(self.owner)
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.business.pk))

    @staticmethod
    def _permission(code):
        permission, _ = Permission.objects.get_or_create(
            code=code.value, defaults={"name": code.label}
        )
        return permission

    @staticmethod
    def _member(business, suffix, permissions, code="OWNER"):
        role = Role.objects.create(
            business=business, name=code.title(), code=code, is_system=True
        )
        for permission in permissions:
            RolePermission.objects.get_or_create(role=role, permission=permission)
        user = User.objects.create_user(
            email=f"{suffix}@example.test", password="not-used-in-test",
            name=suffix, number=f"88{len(suffix)}{business.pk}{suffix}",
        )
        Membership.objects.create(user=user, business=business, role=role, is_active=True)
        return user

    def test_requires_explicit_business_context_and_denies_foreign_business(self):
        self.client.credentials()
        missing = self.client.get("/api/catalog/products/")
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(missing.data["code"], "BUSINESS_CONTEXT_REQUIRED")

        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.other_business.pk))
        foreign = self.client.get("/api/catalog/products/")
        self.assertEqual(foreign.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(foreign.data["code"], "BUSINESS_ACCESS_DENIED")

    def test_product_create_list_detail_and_update(self):
        created = self.client.post("/api/catalog/products/", {
            "name": "  Espresso  ", "sku": " ESP-01 ", "category": "Coffee",
            "description": "Double shot", "status": "active",
        }, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["name"], "Espresso")
        self.assertEqual(created.data["sku"], "ESP-01")
        product_id = created.data["id"]

        listing = self.client.get("/api/catalog/products/?search=esp&status=active")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], product_id)
        self.assertEqual(self.client.get(f"/api/catalog/products/{product_id}/").status_code, 200)

        updated = self.client.patch(
            f"/api/catalog/products/{product_id}/",
            {"status": "archived", "description": "Retired"}, format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["status"], "archived")
        self.assertTrue(Product.objects.filter(pk=product_id, business=self.business).exists())

    def test_sku_is_unique_per_business_and_blank_sku_is_allowed(self):
        payload = {"name": "Latte", "sku": "LATTE-01"}
        self.assertEqual(self.client.post("/api/catalog/products/", payload, format="json").status_code, 201)
        duplicate = self.client.post(
            "/api/catalog/products/", {**payload, "name": "Another Latte"}, format="json"
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        blank = self.client.post(
            "/api/catalog/products/", {"name": "Tea", "sku": "   "}, format="json"
        )
        self.assertEqual(blank.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.other_owner)
        self.client.credentials(HTTP_X_BUSINESS_ID=str(self.other_business.pk))
        same_sku = self.client.post("/api/catalog/products/", payload, format="json")
        self.assertEqual(same_sku.status_code, status.HTTP_201_CREATED)

    def test_permissions_are_enforced(self):
        self.client.force_authenticate(self.viewer)
        denied_create = self.client.post(
            "/api/catalog/products/", {"name": "Forbidden"}, format="json"
        )
        self.assertEqual(denied_create.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get("/api/catalog/products/").status_code, status.HTTP_200_OK)

    def test_rejects_unknown_and_invalid_fields(self):
        unknown = self.client.post(
            "/api/catalog/products/", {"name": "Coffee", "business_id": self.other_business.pk}, format="json"
        )
        self.assertEqual(unknown.status_code, status.HTTP_400_BAD_REQUEST)
        invalid_status = self.client.post(
            "/api/catalog/products/", {"name": "Coffee", "status": "available"}, format="json"
        )
        self.assertEqual(invalid_status.status_code, status.HTTP_400_BAD_REQUEST)


    def test_product_restrictions_create_and_read(self):
        response = self.client.post("/api/catalog/products/", {
            "name": "Almond drink",
            "status": "active",
            "allergens": [
                {"code": "tree_nuts", "presence": "contains"},
                {"code": "soybeans", "presence": "may_contain"},
            ],
            "dietary_tags": ["vegan", "gluten_free"],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["allergens"],
            [
                {"code": "soybeans", "presence": "may_contain"},
                {"code": "tree_nuts", "presence": "contains"},
            ],
        )
        self.assertEqual(response.data["dietary_tags"], ["gluten_free", "vegan"])

        product_id = response.data["id"]
        listed = self.client.get("/api/catalog/products/")
        item = next(row for row in listed.data["results"] if row["id"] == product_id)
        self.assertEqual(item["dietary_tags"], ["gluten_free", "vegan"])

    def test_product_restrictions_patch_replaces_only_supplied_groups(self):
        product = Product.objects.create(
            business=self.business, name="Oat drink", status=Product.Status.ACTIVE
        )
        from catalog.models import ProductAllergen, ProductDietaryTag
        ProductAllergen.objects.create(product=product, code="soybeans", presence="contains")
        ProductDietaryTag.objects.create(product=product, code="vegan")

        response = self.client.patch(
            f"/api/catalog/products/{product.pk}/",
            {"allergens": [], "dietary_tags": ["vegetarian", "gluten_free"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["allergens"], [])
        self.assertEqual(response.data["dietary_tags"], ["gluten_free", "vegetarian"])

    def test_product_restrictions_reject_unknown_and_duplicate_codes(self):
        unknown = self.client.post("/api/catalog/products/", {
            "name": "Unknown allergen",
            "allergens": [{"code": "imaginary_allergen", "presence": "contains"}],
        }, format="json")
        self.assertEqual(unknown.status_code, status.HTTP_400_BAD_REQUEST)

        duplicate = self.client.post("/api/catalog/products/", {
            "name": "Duplicate allergen",
            "allergens": [
                {"code": "milk", "presence": "contains"},
                {"code": "milk", "presence": "may_contain"},
            ],
        }, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        duplicate_tag = self.client.post("/api/catalog/products/", {
            "name": "Duplicate dietary tag",
            "dietary_tags": ["vegan", "vegan"],
        }, format="json")
        self.assertEqual(duplicate_tag.status_code, status.HTTP_400_BAD_REQUEST)

    def test_product_restrictions_are_business_scoped(self):
        product = Product.objects.create(
            business=self.other_business, name="Other business product"
        )
        response = self.client.get(f"/api/catalog/products/{product.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_product_restriction_enum_values_are_enforced_by_database(self):
        product = Product.objects.create(business=self.business, name="Constraint test")

        invalid_rows = (
            lambda: ProductAllergen.objects.create(
                product=product, code="not_an_allergen", presence="contains",
            ),
            lambda: ProductAllergen.objects.create(
                product=product, code="milk", presence="unknown_presence",
            ),
            lambda: ProductDietaryTag.objects.create(
                product=product, code="not_a_dietary_tag",
            ),
        )
        for create_invalid_row in invalid_rows:
            with self.subTest(write=create_invalid_row):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        create_invalid_row()
