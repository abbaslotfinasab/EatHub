from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Business, Membership, Permission, Role, RolePermission, User
from accounts.services.business_service import BusinessService
from accounts.services.rbac_initializer import RBACInitializer, ROLE_PERMISSIONS
from core.enums import PermissionCode


BUSINESS_CREATE_URL = "/api/accounts/create/business/"
REGISTER_URL = "/api/accounts/auth/register/"


def expected_role_permissions(role_code):
    return {
        permission.value if isinstance(permission, PermissionCode) else permission
        for permission in ROLE_PERMISSIONS[role_code]
    }


class RBACInitializerSafetyTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="RBAC Initializer Test")
        self.create_all_permissions()

    @staticmethod
    def create_all_permissions():
        for permission_code in PermissionCode:
            Permission.objects.get_or_create(
                code=permission_code.value,
                defaults={"name": permission_code.label},
            )

    def test_repeated_initialization_is_idempotent(self):
        RBACInitializer.initialize(self.business)
        first_permission_records = set(Permission.objects.values_list("code", "name"))
        first_assignments = set(
            RolePermission.objects.filter(role__business=self.business)
            .values_list("role__code", "permission__code")
        )

        RBACInitializer.initialize(self.business)

        second_permission_records = set(Permission.objects.values_list("code", "name"))
        second_assignments = set(
            RolePermission.objects.filter(role__business=self.business)
            .values_list("role__code", "permission__code")
        )
        self.assertEqual(second_permission_records, first_permission_records)
        self.assertEqual(Permission.objects.count(), len(first_permission_records))
        self.assertEqual(second_assignments, first_assignments)
        self.assertEqual(
            RolePermission.objects.filter(role__business=self.business).count(),
            len(first_assignments),
        )
        self.assertEqual(Role.objects.filter(business=self.business).count(), len(ROLE_PERMISSIONS))

    def test_existing_extra_assignment_is_preserved(self):
        RBACInitializer.initialize(self.business)
        accountant = Role.objects.get(business=self.business, code="ACCOUNTANT")
        extra_permission = Permission.objects.get(code=PermissionCode.PRODUCTS_DELETE)
        RolePermission.objects.create(role=accountant, permission=extra_permission)

        RBACInitializer.initialize(self.business)

        self.assertTrue(
            RolePermission.objects.filter(
                role=accountant,
                permission=extra_permission,
            ).exists()
        )

    def test_custom_role_and_assignments_are_untouched(self):
        RBACInitializer.initialize(self.business)
        custom_role = Role.objects.create(
            business=self.business,
            name="Custom Finance",
            code="CUSTOM_FINANCE",
            is_system=False,
        )
        custom_permission = Permission.objects.get(code=PermissionCode.PRODUCTS_DELETE)
        assignment = RolePermission.objects.create(role=custom_role, permission=custom_permission)

        RBACInitializer.initialize(self.business)

        self.assertTrue(Role.objects.filter(pk=custom_role.pk, is_system=False).exists())
        self.assertTrue(RolePermission.objects.filter(pk=assignment.pk).exists())
        self.assertEqual(
            RolePermission.objects.filter(role=custom_role).values_list(
                "permission__code", flat=True
            ).get(),
            PermissionCode.PRODUCTS_DELETE,
        )

    def test_non_system_role_using_reserved_code_fails_without_mutation(self):
        custom_role = Role.objects.create(
            business=self.business,
            name="Custom Accountant",
            code="ACCOUNTANT",
            is_system=False,
        )
        assigned_permission = Permission.objects.get(code=PermissionCode.PRODUCTS_DELETE)
        assignment = RolePermission.objects.create(role=custom_role, permission=assigned_permission)

        with self.assertRaisesMessage(ValueError, "non-system roles use reserved codes: ACCOUNTANT"):
            RBACInitializer.initialize(self.business)

        self.assertEqual(Role.objects.filter(business=self.business).count(), 1)
        self.assertTrue(RolePermission.objects.filter(pk=assignment.pk).exists())

    def test_missing_permission_is_created_with_canonical_name_and_granted(self):
        Permission.objects.filter(code=PermissionCode.PRODUCTS_DELETE).delete()

        RBACInitializer.initialize(self.business)

        permission = Permission.objects.get(code=PermissionCode.PRODUCTS_DELETE)
        self.assertEqual(permission.name, PermissionCode.PRODUCTS_DELETE.label)
        owner = Role.objects.get(business=self.business, code="OWNER")
        self.assertTrue(RolePermission.objects.filter(role=owner, permission=permission).exists())

    def test_existing_permission_name_is_preserved(self):
        permission = Permission.objects.get(code=PermissionCode.ORDERS_UPDATE)
        permission.name = "Existing local label"
        permission.save(update_fields=["name"])

        RBACInitializer.initialize(self.business)

        permission.refresh_from_db()
        self.assertEqual(permission.name, "Existing local label")

    def test_all_system_roles_receive_only_their_configured_permissions(self):
        RBACInitializer.initialize(self.business)

        for role_code, configured_permissions in ROLE_PERMISSIONS.items():
            role = Role.objects.get(business=self.business, code=role_code)
            expected = {
                permission.value if isinstance(permission, PermissionCode) else permission
                for permission in configured_permissions
            }
            actual = set(
                RolePermission.objects.filter(role=role)
                .values_list("permission__code", flat=True)
            )
            self.assertSetEqual(actual, expected, role_code)

        owner = Role.objects.get(business=self.business, code="OWNER")
        self.assertSetEqual(
            set(RolePermission.objects.filter(role=owner).values_list("permission__code", flat=True)),
            {permission.value for permission in PermissionCode},
        )


class BusinessCreationRBACTests(TestCase):
    def setUp(self):
        # Data migrations may seed the shared permission catalog; model a fresh
        # catalog explicitly in the isolated test database.
        Permission.objects.all().delete()
        self.user = User.objects.create_user(
            email="owner@example.test",
            password="test-password",
            name="Business Owner",
            number="test-owner-1",
        )

    def test_business_creation_seeds_permissions_and_assigns_complete_owner_membership(self):
        self.assertFalse(Permission.objects.exists())

        business = BusinessService.create_business(self.user, "New Cafe")

        self.assertEqual(Permission.objects.count(), len(PermissionCode))
        for permission_code in PermissionCode:
            permission = Permission.objects.get(code=permission_code.value)
            self.assertEqual(permission.name, permission_code.label)

        membership = Membership.objects.get(user=self.user, business=business)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.role.code, "OWNER")
        owner_grants = set(
            RolePermission.objects.filter(role=membership.role)
            .values_list("permission__code", flat=True)
        )
        self.assertSetEqual(owner_grants, {permission.value for permission in PermissionCode})

    def test_business_creation_rolls_back_business_permissions_roles_and_membership_on_failure(self):
        original_save = RolePermission.save
        save_count = 0

        def save_then_fail(instance, *args, **kwargs):
            nonlocal save_count
            save_count += 1
            if save_count == 2:
                raise RuntimeError("simulated business RBAC failure")
            return original_save(instance, *args, **kwargs)

        with patch.object(RolePermission, "save", autospec=True, side_effect=save_then_fail):
            with self.assertRaisesMessage(RuntimeError, "simulated business RBAC failure"):
                BusinessService.create_business(self.user, "Rolled Back Cafe")

        self.assertFalse(Business.objects.filter(name="Rolled Back Cafe").exists())
        self.assertFalse(Permission.objects.exists())
        self.assertFalse(Role.objects.exists())
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.assertFalse(RolePermission.objects.exists())


class BusinessOnboardingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Keep onboarding coverage independent of migration-seeded permissions.
        Permission.objects.all().delete()

    @staticmethod
    def create_user(suffix):
        return User.objects.create_user(
            email=f"onboarding-{suffix}@example.test",
            password="test-password",
            name="Onboarding Test User",
            number=f"onboarding-{suffix}",
        )

    def create_business_through_api(self, user, name):
        self.client.force_authenticate(user=user)
        response = self.client.post(
            BUSINESS_CREATE_URL,
            {"name": name, "number": f"{name.lower().replace(' ', '-')}-phone"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        return Business.objects.get(pk=response.data["id"])

    def test_registration_then_onboarding_creates_complete_owner_context_from_empty_catalog(self):
        registration = self.client.post(
            REGISTER_URL,
            {
                "email": "new-owner@example.test",
                "password": "test-password",
                "name": "New Owner",
                "number": "new-owner-phone",
            },
            format="json",
        )
        self.assertEqual(registration.status_code, 200)
        creator = User.objects.get(email="new-owner@example.test")
        self.assertFalse(Business.objects.exists())
        self.assertFalse(Membership.objects.filter(user=creator).exists())
        self.assertFalse(Permission.objects.exists())

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {registration.data['access']}"
        )
        response = self.client.post(
            BUSINESS_CREATE_URL,
            {"name": "New Cafe", "number": "new-cafe-phone"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        business = Business.objects.get(pk=response.data["id"])
        membership = Membership.objects.get(user=creator, business=business)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.role.code, "OWNER")
        self.assertTrue(membership.role.is_system)

        expected_codes = {permission.value for permission in PermissionCode}
        catalog = {permission.code: permission.name for permission in Permission.objects.all()}
        self.assertSetEqual(set(catalog), expected_codes)
        self.assertEqual(
            catalog,
            {permission.value: permission.label for permission in PermissionCode},
        )
        owner_codes = set(
            RolePermission.objects.filter(role=membership.role)
            .values_list("permission__code", flat=True)
        )
        self.assertSetEqual(owner_codes, expected_role_permissions("OWNER"))
        self.assertIn(PermissionCode.ORDERS_UPDATE, owner_codes)

        for role_code, expected in ROLE_PERMISSIONS.items():
            role = Role.objects.get(business=business, code=role_code.value)
            actual = set(
                RolePermission.objects.filter(role=role)
                .values_list("permission__code", flat=True)
            )
            configured = {
                permission.value if isinstance(permission, PermissionCode) else permission
                for permission in expected
            }
            self.assertSetEqual(actual, configured, role_code.value)

    def test_unauthenticated_and_invalid_business_requests_do_not_create_records(self):
        unauthenticated = self.client.post(
            BUSINESS_CREATE_URL,
            {"name": "Unauthorized Cafe"},
            format="json",
        )
        self.assertEqual(unauthenticated.status_code, 401)
        self.assertFalse(Business.objects.exists())
        self.assertFalse(Permission.objects.exists())

        creator = self.create_user("invalid")
        self.client.force_authenticate(user=creator)
        invalid = self.client.post(
            BUSINESS_CREATE_URL,
            {"address": "Missing required name"},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(Business.objects.exists())
        self.assertFalse(Membership.objects.exists())
        self.assertFalse(Permission.objects.exists())

    def test_business_role_grants_are_isolated_between_businesses(self):
        first_creator = self.create_user("first")
        second_creator = self.create_user("second")
        first_business = self.create_business_through_api(first_creator, "First Cafe")
        second_business = self.create_business_through_api(second_creator, "Second Cafe")

        first_owner = Role.objects.get(business=first_business, code="OWNER")
        second_owner = Role.objects.get(business=second_business, code="OWNER")
        custom_permission = Permission.objects.create(
            code="tests.business_private",
            name="Private test permission",
        )
        RolePermission.objects.create(role=first_owner, permission=custom_permission)

        self.assertTrue(RolePermission.objects.filter(role=first_owner, permission=custom_permission).exists())
        self.assertFalse(RolePermission.objects.filter(role=second_owner, permission=custom_permission).exists())
        for role_code, configured in ROLE_PERMISSIONS.items():
            second_role = Role.objects.get(business=second_business, code=role_code.value)
            actual = set(
                RolePermission.objects.filter(role=second_role)
                .values_list("permission__code", flat=True)
            )
            expected = {
                permission.value if isinstance(permission, PermissionCode) else permission
                for permission in configured
            }
            self.assertSetEqual(actual, expected, role_code.value)

    def test_api_business_creation_failure_rolls_back_business_membership_and_rbac(self):
        creator = self.create_user("rollback")
        self.client.force_authenticate(user=creator)
        self.client.raise_request_exception = False
        original_save = RolePermission.save
        save_count = 0

        def save_then_fail(instance, *args, **kwargs):
            nonlocal save_count
            save_count += 1
            if save_count == 2:
                raise RuntimeError("simulated onboarding RBAC failure")
            return original_save(instance, *args, **kwargs)

        with patch.object(RolePermission, "save", autospec=True, side_effect=save_then_fail):
            response = self.client.post(
                BUSINESS_CREATE_URL,
                {"name": "Rollback Cafe"},
                format="json",
            )

        self.assertEqual(response.status_code, 500)
        self.assertFalse(Business.objects.filter(name="Rollback Cafe").exists())
        self.assertFalse(Membership.objects.filter(user=creator).exists())
        self.assertFalse(Role.objects.exists())
        self.assertFalse(RolePermission.objects.exists())
        self.assertFalse(Permission.objects.exists())
