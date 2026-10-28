from importlib import import_module

from django.test import SimpleTestCase
from django.db import migrations, models
from rest_framework import serializers

from inventory.presentation.reservation_views import (
    MAX_POSITIVE_BIG_INTEGER,
    PositiveBigIntegerIdentifierField,
    ReservationCreateSerializer,
    ReservationListQuerySerializer,
)


class ReservationIdentifierFieldTests(SimpleTestCase):
    def test_positive_bigint_field_accepts_maximum_and_rejects_out_of_range_values(self):
        field = PositiveBigIntegerIdentifierField()
        self.assertEqual(field.run_validation(MAX_POSITIVE_BIG_INTEGER), MAX_POSITIVE_BIG_INTEGER)
        self.assertEqual(field.run_validation(str(MAX_POSITIVE_BIG_INTEGER)), MAX_POSITIVE_BIG_INTEGER)

        for value in (MAX_POSITIVE_BIG_INTEGER + 1, 0, -1, True, 1.5, "1.5", "1e2"):
            with self.subTest(value=value), self.assertRaises(serializers.ValidationError):
                field.run_validation(value)

    def test_manual_create_payload_is_valid_without_source_references(self):
        serializer = ReservationCreateSerializer(data={
            "warehouse_id": 1,
            "reason": "Manual hold",
            "idempotency_key": "123e4567-e89b-12d3-a456-426614174000",
            "lines": [{"ingredient_id": 1, "quantity": "1", "unit": "kg"}],
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["source_type"], "manual")
        self.assertNotIn("source_id", serializer.validated_data)

    def test_manual_create_rejects_external_source_types_and_identifiers(self):
        base = {
            "warehouse_id": 1,
            "reason": "Manual hold",
            "idempotency_key": "123e4567-e89b-12d3-a456-426614174000",
            "lines": [{"ingredient_id": 1, "quantity": "1", "unit": "kg"}],
        }
        for extra in (
            {"source_type": "order"},
            {"source_id": 1},
            {"lines": [{"ingredient_id": 1, "source_line_id": 1, "quantity": "1", "unit": "kg"}]},
        ):
            with self.subTest(extra=extra):
                serializer = ReservationCreateSerializer(data={**base, **extra})
                self.assertFalse(serializer.is_valid())

    def test_list_source_filter_uses_the_same_positive_bigint_boundary(self):
        serializer = ReservationListQuerySerializer(data={
            "source_id": str(MAX_POSITIVE_BIG_INTEGER),
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["source_id"], MAX_POSITIVE_BIG_INTEGER)

        invalid = ReservationListQuerySerializer(data={"source_id": MAX_POSITIVE_BIG_INTEGER + 1})
        self.assertFalse(invalid.is_valid())


class ReservationStatusConstraintDeclarationTests(SimpleTestCase):
    def test_status_check_is_present_in_model_state(self):
        from inventory.infrastructure.django.models import InventoryReservation

        constraints = {item.name: item for item in InventoryReservation._meta.constraints}
        self.assertIn("inv_res_status_ck", constraints)
        expected = models.Q(status__in=("active", "released"))
        self.assertEqual(constraints["inv_res_status_ck"].condition, expected)

        migration = import_module(
            "inventory.migrations.0013_reservation_status_constraint"
        ).Migration
        migration_constraints = [
            operation.constraint
            for operation in migration.operations
            if isinstance(operation, migrations.AddConstraint)
            and operation.constraint.name == "inv_res_status_ck"
        ]
        self.assertEqual(len(migration_constraints), 1)
        self.assertEqual(migration_constraints[0].condition, expected)
