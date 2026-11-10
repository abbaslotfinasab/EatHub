from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from catalog.models import Product
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
