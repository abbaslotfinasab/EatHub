from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

from django.db import models
from django.test import SimpleTestCase


class MultiActiveMembershipMigrationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.migration = import_module("accounts.migrations.0016_multi_active_memberships")

    def test_migration_removes_user_wide_active_constraint_and_adds_pair_uniqueness(self):
        operations = self.migration.Migration.operations

        self.assertEqual(operations[1].name, "one_active_business_per_user")
        self.assertEqual(operations[2].constraint.name, "unique_user_business_membership")
        self.assertEqual(
            tuple(operations[2].constraint.fields),
            ("user", "business"),
        )
        self.assertIsInstance(operations[2].constraint, models.UniqueConstraint)

    def test_forward_guard_rejects_duplicate_user_business_rows(self):
        self._assert_guard_rejects_duplicates(
            self.migration.ensure_memberships_are_unique_per_business,
            {"user_id": 17, "business_id": 29},
        )

    def test_forward_guard_allows_clean_membership_pairs(self):
        self._assert_guard_allows_clean_data(
            self.migration.ensure_memberships_are_unique_per_business,
        )

    def test_reverse_guard_rejects_multiple_active_memberships_before_constraint_restore(self):
        self._assert_guard_rejects_duplicates(
            self.migration.ensure_single_active_membership_per_user,
            {"user_id": 17},
        )
        reverse_guard = self.migration.Migration.operations[3]
        self.assertIs(reverse_guard.reverse_code, self.migration.ensure_single_active_membership_per_user)

    def _assert_guard_rejects_duplicates(self, guard, sample):
        queryset = Mock()
        queryset.exists.return_value = True
        queryset.first.return_value = sample
        manager = Mock()
        manager.using.return_value = queryset
        queryset.values.return_value = queryset
        queryset.annotate.return_value = queryset
        queryset.filter.return_value = queryset
        Membership = SimpleNamespace(objects=manager)
        apps = Mock()
        apps.get_model.return_value = Membership
        schema_editor = SimpleNamespace(connection=SimpleNamespace(alias="default"))

        with self.assertRaises(RuntimeError):
            guard(apps, schema_editor)

    def _assert_guard_allows_clean_data(self, guard):
        queryset = Mock()
        queryset.exists.return_value = False
        manager = Mock()
        manager.using.return_value = queryset
        queryset.values.return_value = queryset
        queryset.annotate.return_value = queryset
        queryset.filter.return_value = queryset
        Membership = SimpleNamespace(objects=manager)
        apps = Mock()
        apps.get_model.return_value = Membership
        schema_editor = SimpleNamespace(connection=SimpleNamespace(alias="default"))

        guard(apps, schema_editor)
