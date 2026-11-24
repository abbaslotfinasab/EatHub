from rest_framework import status
from rest_framework.test import APITestCase

from accounts.enums import RoleCode
from accounts.models import Business, Membership, Role, User
from accounts.services.rbac_initializer import RBACInitializer
from purchase.models import Supplier


class SupplierManagementAPITests(APITestCase):
    endpoint = "/api/purchase/suppliers/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="supplier-manager@example.com",
            password="password",
            name="Supplier Manager",
            number="9401",
        )
        self.business = Business.objects.create(name="Supplier API Business")
        self.other_business = Business.objects.create(name="Other Supplier Business")
        role = Role.objects.create(
            business=self.business,
            name="Owner",
            code=RoleCode.OWNER,
            is_system=True,
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=role,
            is_active=True,
        )
        RBACInitializer.initialize(self.business)
        self.client.force_authenticate(self.user)

    def create_supplier(self, business, name, **kwargs):
        return Supplier.objects.create(business=business, name=name, **kwargs)

    def payload(self, **overrides):
        data = {
            "name": "Fresh Produce Co.",
            "phone": "02112345678",
            "email": "sales@example.com",
            "address": "Main street",
            "tax_number": "TAX-9401",
            "notes": "Preferred supplier",
        }
        data.update(overrides)
        return data

    def test_list_search_and_active_filter_are_scoped_to_active_business(self):
        active = self.create_supplier(self.business, "Fresh Produce Co.", phone="02112345678")
        inactive = self.create_supplier(self.business, "Inactive Produce", is_active=False)
        self.create_supplier(self.other_business, "Fresh Produce Co.", phone="02112345678")

        listing = self.client.get(self.endpoint)
        searched = self.client.get(self.endpoint, {"search": "Fresh Produce"})
        inactive_listing = self.client.get(self.endpoint, {"is_active": "false"})

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in listing.data], [active.id, inactive.id])
        self.assertEqual(searched.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in searched.data], [active.id])
        self.assertEqual(inactive_listing.status_code, status.HTTP_200_OK)
        self.assertEqual([row["id"] for row in inactive_listing.data], [inactive.id])
        self.assertTrue(all(row["business_id"] == self.business.id for row in listing.data))

    def test_create_and_update_supplier(self):
        created = self.client.post(self.endpoint, self.payload(), format="json")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["business_id"], self.business.id)
        self.assertEqual(created.data["name"], "Fresh Produce Co.")

        updated = self.client.put(
            f"{self.endpoint}{created.data['id']}/",
            self.payload(name="Updated Produce Co.", is_active=False),
            format="json",
        )

        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["name"], "Updated Produce Co.")
        self.assertFalse(updated.data["is_active"])

    def test_create_ignores_client_business_id_and_rejects_invalid_email(self):
        created = self.client.post(
            self.endpoint,
            self.payload(business_id=self.other_business.id),
            format="json",
        )
        invalid = self.client.post(
            self.endpoint,
            self.payload(name="Invalid Email Supplier", email="not-an-email"),
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["business_id"], self.business.id)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            Supplier.objects.filter(
                business=self.other_business,
                name="Fresh Produce Co.",
            ).exists()
        )

    def test_detail_hides_supplier_from_another_business(self):
        foreign = self.create_supplier(self.other_business, "Foreign Supplier")

        response = self.client.get(f"{self.endpoint}{foreign.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_supplier_management_requires_manage_permission(self):
        accountant_role = Role.objects.get(
            business=self.business,
            code=RoleCode.ACCOUNTANT,
        )
        accountant = User.objects.create_user(
            email="supplier-read-only@example.com",
            password="password",
            name="Read Only Accountant",
            number="9402",
        )
        Membership.objects.create(
            user=accountant,
            business=self.business,
            role=accountant_role,
            is_active=True,
        )
        self.client.force_authenticate(accountant)

        response = self.client.post(self.endpoint, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
