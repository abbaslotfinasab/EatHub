from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError, connection, transaction
from django.test import TestCase

from accounts.models import Business
from inventory.application.exceptions import OperationConflict
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.enums.movement import MovementDirection
from inventory.domain.exceptions import InvalidQuantity, TenantMismatch
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.reversal_context import ReversalContext
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost
from inventory.infrastructure.django.mappers import (
    PersistenceMappingError,
    ingredient_to_domain,
    movement_to_domain,
    movement_to_orm,
    stock_to_domain,
    stock_to_orm,
    warehouse_to_domain,
)
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockBalanceRepository,
    DjangoStockMovementRepository,
    DjangoStockRepository,
    DjangoWarehouseRepository,
)
from inventory.application.dto.stock_balance import ListStockBalancesQuery
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.models import Ingredient as LegacyIngredient
from inventory.models import Warehouse as LegacyWarehouse


class InventoryPersistenceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.business = Business.objects.create(name="Primary", slug="primary-test")
        cls.other_business = Business.objects.create(name="Other", slug="other-test")
        cls.warehouse_row = LegacyWarehouse.objects.create(
            business=cls.business, name="Main", code="MAIN", is_default=True
        )
        cls.ingredient_row = LegacyIngredient.objects.create(
            business=cls.business,
            name="Flour",
            unit=Unit.KG.value,
            preparation_level="raw",
        )
        cls.foreign_warehouse_row = LegacyWarehouse.objects.create(
            business=cls.other_business, name="Foreign"
        )
        cls.foreign_ingredient_row = LegacyIngredient.objects.create(
            business=cls.other_business,
            name="Rice",
            unit=Unit.KG.value,
            preparation_level="raw",
        )

    def setUp(self) -> None:
        self.ingredients = DjangoIngredientRepository()
        self.warehouses = DjangoWarehouseRepository()
        self.stocks = DjangoStockRepository()
        self.movements = DjangoStockMovementRepository()
        self.business_id = self.business.pk
        self.warehouse = self.warehouses.get_by_id_for_business(
            self.warehouse_row.pk, self.business_id
        )
        self.ingredient = self.ingredients.get_by_id_for_business(
            self.ingredient_row.pk, self.business_id
        )

    def source(self, line_id: int, operation: str = "receive_stock") -> SourceIdentity:
        return SourceIdentity(self.business_id, "receipt", 200, line_id, operation)

    def _receive_movement(self, line_id: int = 1):
        stock = self.stocks.get_or_create_for_business(
            self.business_id, self.warehouse, self.ingredient
        )
        movement = stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("2"),
            self.source(line_id),
            self.warehouse,
        )
        self.stocks.save(stock)
        return stock, movement

    @staticmethod
    def _integrity_error_with_driver_metadata(
        sqlstate: str, constraint_name: str
    ) -> IntegrityError:
        error = IntegrityError("simulated database integrity error")
        driver_error = Exception("simulated psycopg error")
        driver_error.pgcode = sqlstate
        driver_error.diag = SimpleNamespace(constraint_name=constraint_name)
        error.__cause__ = driver_error
        return error

    def test_master_repositories_are_business_scoped(self) -> None:
        self.assertIsNone(
            self.ingredients.get_by_id_for_business(
                self.ingredient_row.pk, self.other_business.pk
            )
        )
        self.assertIsNone(
            self.warehouses.get_by_id_for_business(
                self.warehouse_row.pk, self.other_business.pk
            )
        )
        self.assertEqual(ingredient_to_domain(self.ingredient_row), self.ingredient)
        self.assertEqual(warehouse_to_domain(self.warehouse_row), self.warehouse)

    def test_stock_round_trip_preserves_decimal_and_reconstitutes_projection(self) -> None:
        stock = self.stocks.get_or_create_for_business(
            self.business_id, self.warehouse, self.ingredient
        )
        stock.receive(
            Quantity(Decimal("123456.123456"), Unit.KG),
            UnitCost("2.123456"),
            self.source(1),
            self.warehouse,
        )
        self.stocks.save(stock)

        row = InventoryV1Stock.objects.get(
            business_id=self.business_id,
            warehouse_id=self.warehouse_row.pk,
            ingredient_id=self.ingredient_row.pk,
        )
        restored = stock_to_domain(row)
        self.assertEqual(restored.quantity.amount, Decimal("123456.123456"))
        self.assertEqual(restored.average_cost.amount, Decimal("2.123456"))

        high_precision = Stock.reconstitute(
            self.warehouse,
            self.ingredient,
            Quantity(Decimal("123456.123456789012"), Unit.KG),
            UnitCost("2.1234567890123456789012345678"),
        )
        mapped = stock_to_orm(high_precision)
        mapped.warehouse = self.warehouse_row
        mapped.ingredient = self.ingredient_row
        exact = stock_to_domain(mapped)
        self.assertEqual(exact.quantity.amount, Decimal("123456.123456789012"))
        self.assertEqual(
            exact.average_cost.amount,
            Decimal("2.1234567890123456789012345678"),
        )
        calculated = Stock(self.warehouse, self.ingredient)
        calculated.receive(
            Quantity(Decimal("1.123456789012"), Unit.KG),
            UnitCost("4.1234567890123456789012345678"),
            self.source(8),
            self.warehouse,
        )
        calculated.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("7"),
            self.source(9),
            self.warehouse,
        )
        calculated_row = stock_to_orm(calculated)
        calculated_row.warehouse = self.warehouse_row
        calculated_row.ingredient = self.ingredient_row
        self.assertEqual(
            stock_to_domain(calculated_row).average_cost,
            calculated.average_cost,
        )
        with self.assertRaises(InvalidQuantity):
            Quantity(Decimal("1.0000000000001"), Unit.KG)

    def test_stock_business_scope_excludes_foreign_rows_and_mapper_rejects_corruption(self) -> None:
        foreign_stock = InventoryV1Stock.objects.create(
            business=self.other_business,
            warehouse=self.foreign_warehouse_row,
            ingredient=self.foreign_ingredient_row,
            unit=Unit.KG.value,
        )
        self.assertIsNone(
            self.stocks.get_for_business(
                self.business_id,
                self.foreign_warehouse_row.pk,
                self.foreign_ingredient_row.pk,
            )
        )

        inconsistent = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse_row,
            ingredient=self.foreign_ingredient_row,
            unit=Unit.KG.value,
        )
        with self.assertRaises(TenantMismatch):
            stock_to_domain(inconsistent)
        self.assertIsNotNone(foreign_stock.pk)

    def test_stock_key_database_uniqueness(self) -> None:
        values = {
            "business": self.business,
            "warehouse": self.warehouse_row,
            "ingredient": self.ingredient_row,
            "unit": Unit.KG.value,
        }
        InventoryV1Stock.objects.create(**values)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InventoryV1Stock.objects.create(**values)

    def test_movement_round_trip_preserves_identity_snapshots_and_order(self) -> None:
        stock = self.stocks.get_or_create_for_business(
            self.business_id, self.warehouse, self.ingredient
        )
        first = stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("4.1234567890123"),
            self.source(1),
            self.warehouse,
            occurred_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
        )
        self.stocks.save(stock)
        self.movements.save(first)
        second = stock.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("7"),
            self.source(2),
            self.warehouse,
        )
        self.stocks.save(stock)
        self.movements.save(second)

        restored = self.movements.find_by_source_identity_for_business(
            self.business_id, second.source_identity
        )
        latest = self.movements.get_latest_effective_for_stock(
            self.business_id, stock.key
        )
        self.assertEqual(restored, second)
        self.assertEqual(restored.quantity.amount, Decimal("2"))
        self.assertEqual(restored.average_cost_before.amount, first.unit_cost.amount)
        self.assertEqual(restored.balance_after.amount, Decimal("3"))
        self.assertEqual(restored.source_identity, second.source_identity)
        self.assertEqual(restored.occurred_at, second.occurred_at)
        self.assertEqual(latest.source_identity, second.source_identity)

        stock_row = InventoryV1Stock.objects.get(
            business_id=self.business_id,
            warehouse_id=self.warehouse_row.pk,
            ingredient_id=self.ingredient_row.pk,
        )
        orm_row = movement_to_orm(first, stock_row)
        self.assertEqual(movement_to_domain(orm_row).source_identity, first.source_identity)

        high_precision_stock = Stock(self.warehouse, self.ingredient)
        high_precision_movement = high_precision_stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("4.1234567890123456789012345678"),
            self.source(3),
            self.warehouse,
        )
        mapped_movement = movement_to_orm(high_precision_movement, stock_row)
        mapped_movement.stock = stock_row
        restored_high_precision = movement_to_domain(mapped_movement)
        self.assertEqual(
            restored_high_precision.unit_cost.amount,
            Decimal("4.1234567890123456789012345678"),
        )

    def test_avco_precision_boundary_maps_and_reconstitutes_exactly(self) -> None:
        precise_cost = Decimal("4." + "1234567890" * 4 + "12345678")
        stock = Stock(self.warehouse, self.ingredient)
        first = stock.receive(
            Quantity(Decimal("1.123456789012"), Unit.KG),
            UnitCost(precise_cost),
            self.source(40),
            self.warehouse,
        )
        prior_average = stock.average_cost
        second = stock.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("7"),
            self.source(41),
            self.warehouse,
        )

        projection_row = stock_to_orm(stock)
        projection_row.warehouse = self.warehouse_row
        projection_row.ingredient = self.ingredient_row
        restored_stock = stock_to_domain(projection_row)
        self.assertEqual(restored_stock.quantity, stock.quantity)
        self.assertEqual(restored_stock.average_cost, stock.average_cost)
        self.assertEqual(restored_stock.average_cost.amount.as_tuple().exponent, -48)

        movement_row = movement_to_orm(second, projection_row)
        movement_row.stock = projection_row
        restored_movement = movement_to_domain(movement_row)
        self.assertEqual(restored_movement, second)
        self.assertEqual(restored_movement.average_cost_before, prior_average)
        self.assertEqual(restored_movement.balance_after, second.balance_after)

        reversal = stock.reverse(
            second,
            self.source(42, "reverse_stock"),
            self.warehouse,
            context=ReversalContext(second.source_identity, False),
        )
        self.assertEqual(stock.average_cost, prior_average)
        reversed_projection = stock_to_orm(stock)
        reversed_projection.warehouse = self.warehouse_row
        reversed_projection.ingredient = self.ingredient_row
        self.assertEqual(stock_to_domain(reversed_projection).average_cost, prior_average)
        reversal_row = movement_to_orm(reversal, reversed_projection)
        reversal_row.stock = reversed_projection
        self.assertEqual(movement_to_domain(reversal_row), reversal)

    def test_movement_mapper_requires_stock_canonical_unit(self) -> None:
        stock = Stock(self.warehouse, self.ingredient)
        movement = stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("3"),
            self.source(50),
            self.warehouse,
        )
        stock_row = stock_to_orm(stock)
        stock_row.warehouse = self.warehouse_row
        stock_row.ingredient = self.ingredient_row

        matching_row = movement_to_orm(movement, stock_row)
        matching_row.stock = stock_row
        self.assertEqual(matching_row.unit, Unit.KG.value)
        self.assertEqual(movement_to_domain(matching_row), movement)

        mismatched = StockMovement.reconstitute(
            stock_key=movement.stock_key,
            movement_type=movement.movement_type,
            direction=movement.direction,
            quantity=Quantity(Decimal("1000"), Unit.G),
            unit_cost=movement.unit_cost,
            source_identity=self.source(51),
            balance_after=Quantity(Decimal("1000"), Unit.G),
            average_cost_before=movement.average_cost_before,
        )
        with self.assertRaises(PersistenceMappingError):
            movement_to_orm(mismatched, stock_row)

        matching_row.unit = Unit.G.value
        with self.assertRaises(PersistenceMappingError):
            movement_to_domain(matching_row)

    def test_source_identity_database_uniqueness_and_repository_conflict(self) -> None:
        stock = self.stocks.get_or_create_for_business(
            self.business_id, self.warehouse, self.ingredient
        )
        movement = stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("2"),
            self.source(1),
            self.warehouse,
        )
        self.stocks.save(stock)
        self.movements.save(movement)
        # SQLite reports only a generic unique-constraint code, so the
        # repository conservatively propagates it. PostgreSQL identifies the
        # named source constraint and maps it to the domain conflict.
        expected_error = (
            OperationConflict if connection.vendor == "postgresql" else IntegrityError
        )
        with self.assertRaises(expected_error):
            self.movements.save(movement)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_named_source_identity_constraint_becomes_operation_conflict(self) -> None:
        _, movement = self._receive_movement()
        database_error = self._integrity_error_with_driver_metadata(
            "23505", "inv_v1_move_source_uq"
        )

        with patch.object(
            InventoryV1StockMovement, "save", side_effect=database_error
        ):
            with self.assertRaises(OperationConflict) as raised:
                self.movements.save(movement)

        self.assertIs(raised.exception.__cause__, database_error)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_named_reversal_target_constraint_becomes_operation_conflict(self) -> None:
        stock, original = self._receive_movement()
        self.movements.save(original)
        reversal = stock.reverse(
            original,
            self.source(2, "reverse_stock"),
            self.warehouse,
            context=ReversalContext(original.source_identity, False),
        )
        self.stocks.save(stock)
        database_error = self._integrity_error_with_driver_metadata(
            "23505", "inv_v1_move_reverse_uq"
        )

        with patch.object(
            InventoryV1StockMovement, "save", side_effect=database_error
        ):
            with self.assertRaises(OperationConflict) as raised:
                self.movements.save(reversal)

        self.assertIs(raised.exception.__cause__, database_error)
        self.assertEqual(InventoryV1StockMovement.objects.count(), 1)

    def test_unrelated_movement_integrity_error_propagates_unchanged(self) -> None:
        _, movement = self._receive_movement()
        for sqlstate, constraint_name in (
            ("23503", "unrelated_foreign_key"),
            ("23514", "unrelated_check_constraint"),
            ("23505", "unrelated_unique_constraint"),
        ):
            with self.subTest(sqlstate=sqlstate, constraint_name=constraint_name):
                integrity_error = self._integrity_error_with_driver_metadata(
                    sqlstate, constraint_name
                )
                with patch.object(
                    InventoryV1StockMovement,
                    "save",
                    side_effect=integrity_error,
                ):
                    with self.assertRaises(IntegrityError) as raised:
                        self.movements.save(movement)

                self.assertIs(raised.exception, integrity_error)
                self.assertEqual(InventoryV1StockMovement.objects.count(), 0)

    def test_reversal_reference_is_persisted_as_a_new_immutable_movement(self) -> None:
        stock = self.stocks.get_or_create_for_business(
            self.business_id, self.warehouse, self.ingredient
        )
        original = stock.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("3.125"),
            self.source(1),
            self.warehouse,
        )
        self.stocks.save(stock)
        self.movements.save(original)
        original_values = (original.balance_after, original.average_cost_before)

        reversal_identity = self.source(2, "reverse_stock")
        reversal = stock.reverse(
            original,
            reversal_identity,
            self.warehouse,
            context=ReversalContext(original.source_identity, False),
        )
        self.stocks.save(stock)
        self.movements.save(reversal)

        restored = self.movements.find_by_source_identity_for_business(
            self.business_id, reversal_identity
        )
        self.assertEqual(restored.reverses, original.source_identity)
        self.assertTrue(
            self.movements.has_reversal_for_source(
                self.business_id, original.source_identity
            )
        )
        self.assertEqual((original.balance_after, original.average_cost_before), original_values)
        self.assertEqual(reversal.direction, MovementDirection.OUT)
        self.assertEqual(
            InventoryV1StockMovement.objects.count(),
            2,
        )

    def test_unit_of_work_rolls_back_stock_persistence(self) -> None:
        unit_of_work = DjangoInventoryUnitOfWork()
        with self.assertRaises(RuntimeError):
            with unit_of_work.atomic():
                InventoryV1Stock.objects.create(
                    business=self.business,
                    warehouse=self.warehouse_row,
                    ingredient=self.ingredient_row,
                    unit=Unit.KG.value,
                )
                raise RuntimeError("rollback test")
        self.assertFalse(InventoryV1Stock.objects.exists())

    def test_stock_balance_repository_returns_bounded_stable_v1_pages(self) -> None:
        warehouses = [self.warehouse_row] + [
            LegacyWarehouse.objects.create(
                business=self.business,
                name=f"Warehouse {index}",
            )
            for index in range(1, 3)
        ]
        rows = [
            InventoryV1Stock.objects.create(
                business=self.business,
                warehouse=warehouse,
                ingredient=self.ingredient_row,
                unit=Unit.KG.value,
                quantity=Decimal(f"{quantity}.5"),
                average_cost=Decimal("12.345678901234"),
            )
            for quantity, warehouse in enumerate(warehouses)
        ]
        repository = DjangoStockBalanceRepository()

        page = repository.list_for_business(
            ListStockBalancesQuery(
                business_id=self.business.pk,
                page=2,
                page_size=2,
            )
        )

        self.assertEqual(page.count, 3)
        self.assertEqual(page.page, 2)
        self.assertEqual(page.page_size, 2)
        self.assertEqual([item.id for item in page.results], [rows[2].pk])
        self.assertEqual(page.results[0].ingredient_name, "Flour")
        self.assertEqual(page.results[0].warehouse_name, "Warehouse 2")
        self.assertEqual(page.results[0].quantity, Decimal("2.5"))
        self.assertEqual(page.results[0].average_cost, Decimal("12.345678901234"))

    def test_stock_balance_repository_scopes_business_and_filters(self) -> None:
        own_stock = InventoryV1Stock.objects.create(
            business=self.business,
            warehouse=self.warehouse_row,
            ingredient=self.ingredient_row,
            unit=Unit.KG.value,
        )
        foreign_stock = InventoryV1Stock.objects.create(
            business=self.other_business,
            warehouse=self.foreign_warehouse_row,
            ingredient=self.foreign_ingredient_row,
            unit=Unit.KG.value,
        )
        repository = DjangoStockBalanceRepository()

        page = repository.list_for_business(
            ListStockBalancesQuery(
                business_id=self.business.pk,
                ingredient_id=self.ingredient_row.pk,
                warehouse_id=self.warehouse_row.pk,
            )
        )

        self.assertEqual(page.count, 1)
        self.assertEqual([item.id for item in page.results], [own_stock.pk])
        self.assertNotIn(foreign_stock.pk, [item.id for item in page.results])
