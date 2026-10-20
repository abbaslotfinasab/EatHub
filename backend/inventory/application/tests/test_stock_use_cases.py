from contextlib import AbstractContextManager
from copy import deepcopy
from decimal import Decimal
from unittest import TestCase

from inventory.application.commands import (
    AdjustStockCommand,
    OperationIdentityInput,
    ReceiveStockCommand,
    ReverseStockMovementCommand,
)
from inventory.application.context import InventoryExecutionContext
from inventory.application.exceptions import (
    InvalidApplicationContext,
    OperationConflict,
    ResourceNotFound,
    StockProjectionConflict,
    WarehouseConfigurationError,
)
from inventory.application.use_cases.adjust_stock import AdjustStockUseCase
from inventory.application.use_cases.receive_stock import ReceiveStockUseCase
from inventory.application.use_cases.reverse_stock_movement import (
    ReverseStockMovementUseCase,
)
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import (
    IncompatibleUnits,
    InactiveWarehouse,
    InvalidQuantity,
    MovementAlreadyReversed,
    MovementNotReversible,
    NegativeStock,
    TenantMismatch,
)
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.participants = []
        self.active = False
        self.committed = 0
        self.rolled_back = 0

    def register(self, participant) -> None:
        self.participants.append(participant)

    def atomic(self) -> AbstractContextManager[None]:
        return _AtomicContext(self)


class _AtomicContext(AbstractContextManager[None]):
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self._unit_of_work = unit_of_work
        self._snapshots = []

    def __enter__(self) -> None:
        self._unit_of_work.active = True
        self._snapshots = [
            participant.snapshot() for participant in self._unit_of_work.participants
        ]

    def __exit__(self, exception_type, exception, traceback) -> bool:
        if exception_type is None:
            self._unit_of_work.committed += 1
        else:
            self._unit_of_work.rolled_back += 1
            for participant, snapshot in zip(
                self._unit_of_work.participants, self._snapshots
            ):
                participant.restore(snapshot)
        self._unit_of_work.active = False
        return False


class FakeWarehouseRepository:
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self.unit_of_work = unit_of_work
        self.rows = {10: Warehouse(10, 1, "Main")}
        self.calls = []

    def get_by_id_for_business(self, warehouse_id: int, business_id: int):
        self.calls.append((warehouse_id, business_id))
        warehouse = self.rows.get(warehouse_id)
        return warehouse if warehouse and warehouse.business_id == business_id else None

    def get_active_defaults_for_business(self, business_id: int):
        return [
            warehouse for warehouse in self.rows.values()
            if warehouse.business_id == business_id
            and warehouse.is_active and warehouse.is_default
        ]


class FakeIngredientRepository:
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self.unit_of_work = unit_of_work
        self.rows = {20: Ingredient(20, 1, "Flour", Unit.KG)}
        self.calls = []

    def get_by_id_for_business(self, ingredient_id: int, business_id: int):
        self.calls.append((ingredient_id, business_id))
        ingredient = self.rows.get(ingredient_id)
        return ingredient if ingredient and ingredient.business_id == business_id else None


class FakeStockRepository:
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self.unit_of_work = unit_of_work
        self.rows: dict[tuple[int, int, int], Stock] = {}
        self.saved: list[Stock] = []
        self.calls = []
        unit_of_work.register(self)

    def snapshot(self):
        return deepcopy((self.rows, self.saved))

    def restore(self, snapshot) -> None:
        self.rows, self.saved = snapshot

    @staticmethod
    def _key(business_id: int, warehouse_id: int, ingredient_id: int):
        return (business_id, warehouse_id, ingredient_id)

    def get_for_business(self, business_id: int, warehouse_id: int, ingredient_id: int):
        self.calls.append(("read", business_id, warehouse_id, ingredient_id))
        return self.rows.get(self._key(business_id, warehouse_id, ingredient_id))

    def get_or_create_for_business(
        self, business_id: int, warehouse: Warehouse, ingredient: Ingredient
    ) -> Stock:
        self.calls.append(("get_or_create", business_id, warehouse.id, ingredient.id))
        key = self._key(business_id, warehouse.id, ingredient.id)
        if key not in self.rows:
            self.rows[key] = Stock(warehouse, ingredient)
        return self.rows[key]

    def save(self, stock: Stock) -> None:
        if not self.unit_of_work.active:
            raise AssertionError("Stock save must be inside Unit of Work.")
        self.rows[(stock.key.business_id, stock.key.warehouse_id, stock.key.ingredient_id)] = stock
        self.saved.append(stock)

    def seed(self, stock: Stock) -> None:
        self.rows[(stock.key.business_id, stock.key.warehouse_id, stock.key.ingredient_id)] = stock


class FakeStockMovementRepository:
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self.unit_of_work = unit_of_work
        self.rows: list[StockMovement] = []
        self.saved: list[StockMovement] = []
        self.fail_on_save = False
        self.calls = []
        unit_of_work.register(self)

    def snapshot(self):
        return deepcopy((self.rows, self.saved))

    def restore(self, snapshot) -> None:
        self.rows, self.saved = snapshot

    def find_by_source_identity_for_business(
        self, business_id: int, source_identity: SourceIdentity
    ) -> StockMovement | None:
        self.calls.append(("find", business_id, source_identity))
        return next(
            (
                movement
                for movement in reversed(self.rows)
                if movement.source_identity == source_identity
                and movement.stock_key.business_id == business_id
            ),
            None,
        )

    def get_latest_effective_for_stock(self, business_id: int, stock_key):
        self.calls.append(("latest", business_id, stock_key))
        return next(
            (
                movement
                for movement in reversed(self.rows)
                if movement.stock_key == stock_key
                and movement.stock_key.business_id == business_id
            ),
            None,
        )

    def has_reversal_for_source(
        self, business_id: int, original_source_identity: SourceIdentity
    ) -> bool:
        self.calls.append(("has_reversal", business_id, original_source_identity))
        return any(
            movement.stock_key.business_id == business_id
            and movement.reverses == original_source_identity
            for movement in self.rows
        )

    def save(self, movement: StockMovement) -> None:
        if not self.unit_of_work.active:
            raise AssertionError("Movement save must be inside Unit of Work.")
        if self.fail_on_save:
            raise RuntimeError("Ledger append failed.")
        self.rows.append(movement)
        self.saved.append(movement)

    def seed(self, movement: StockMovement) -> None:
        self.rows.append(movement)


class InventoryApplicationTests(TestCase):
    def setUp(self) -> None:
        self.context = InventoryExecutionContext(business_id=1, actor_id=77)
        self.unit_of_work = FakeUnitOfWork()
        self.warehouses = FakeWarehouseRepository(self.unit_of_work)
        self.ingredients = FakeIngredientRepository(self.unit_of_work)
        self.stocks = FakeStockRepository(self.unit_of_work)
        self.movements = FakeStockMovementRepository(self.unit_of_work)
        self.receive = ReceiveStockUseCase(
            self.warehouses,
            self.ingredients,
            self.stocks,
            self.movements,
            self.unit_of_work,
        )
        self.adjust = AdjustStockUseCase(
            self.warehouses,
            self.ingredients,
            self.stocks,
            self.movements,
            self.unit_of_work,
        )
        self.reverse = ReverseStockMovementUseCase(
            self.warehouses,
            self.ingredients,
            self.stocks,
            self.movements,
            self.unit_of_work,
        )

    @staticmethod
    def operation(
        source_type: str = "purchase_goods_receipt",
        document_id: int = 100,
        line_id: int = 1,
        kind: str = "receive_stock",
    ) -> OperationIdentityInput:
        return OperationIdentityInput(source_type, document_id, line_id, kind)

    def receive_command(self, **changes) -> ReceiveStockCommand:
        values = {
            "warehouse_id": 10,
            "ingredient_id": 20,
            "quantity_amount": Decimal("4"),
            "quantity_unit": Unit.KG.value,
            "unit_cost_amount": Decimal("3"),
            "unit_cost_unit": Unit.KG.value,
            "source": self.operation(),
        }
        values.update(changes)
        return ReceiveStockCommand(**values)

    def adjust_command(self, **changes) -> AdjustStockCommand:
        values = {
            "warehouse_id": 10,
            "ingredient_id": 20,
            "quantity": Quantity(Decimal("1"), Unit.KG),
            "direction": MovementDirection.IN,
            "reason": "Physical count",
            "source": self.operation("inventory_adjustment", 200, 1, "adjust_stock"),
        }
        values.update(changes)
        return AdjustStockCommand(**values)

    def reverse_command(self, original: StockMovement, **changes):
        values = {
            "target": OperationIdentityInput(
                original.source_identity.source_type,
                original.source_identity.source_document_id,
                original.source_identity.source_line_id,
                original.source_identity.operation_kind,
            ),
            "source": self.operation("inventory_reversal", 300, 1, "reverse_movement"),
            "reason": "Correction",
        }
        values.update(changes)
        return ReverseStockMovementCommand(**values)

    def seed_stock(self, quantity: str = "0", cost: str = "0") -> Stock:
        stock = Stock(self.warehouses.rows[10], self.ingredients.rows[20])
        if Decimal(quantity) > 0:
            stock.receive(
                Quantity(Decimal(quantity), Unit.KG),
                UnitCost(cost),
                SourceIdentity(1, "seed", 1, 1, "seed_stock"),
                self.warehouses.rows[10],
            )
        self.stocks.seed(stock)
        return stock

    def test_receive_new_stock_persists_projection_and_movement_atomically(self) -> None:
        result = self.receive.execute(self.receive_command(), self.context)
        self.assertEqual(result.current_quantity, Quantity(Decimal("4"), Unit.KG))
        self.assertEqual(result.current_average_cost, UnitCost("3"))
        self.assertFalse(result.idempotent)
        self.assertEqual(len(self.stocks.saved), 1)
        self.assertEqual(len(self.movements.saved), 1)
        self.assertEqual(self.unit_of_work.committed, 1)
        self.assertEqual(self.unit_of_work.rolled_back, 0)

    def test_purchase_unit_quantity_and_cost_normalize_to_canonical_unit(self) -> None:
        self.ingredients.rows[20] = Ingredient(20, 1, "Flour", Unit.KG)
        self.warehouses.rows[10] = Warehouse(10, 1, "Main", is_default=True)
        result = self.receive.execute(
            self.receive_command(
                warehouse_id=None,
                quantity_amount=Decimal("500"),
                quantity_unit=Unit.G.value,
                unit_cost_amount=Decimal("150"),
                unit_cost_unit=Unit.G.value,
            ),
            self.context,
        )
        self.assertEqual(result.current_quantity, Quantity(Decimal("0.5"), Unit.KG))
        self.assertEqual(result.current_average_cost, UnitCost("150000"))
        self.assertEqual(self.movements.saved[-1].quantity, Quantity("0.5", Unit.KG))
        self.assertEqual(self.movements.saved[-1].unit_cost, UnitCost("150000"))
        self.assertEqual(self.movements.saved[-1].actor_id, 77)

    def test_supported_purchase_unit_normalization_matrix(self) -> None:
        cases = (
            (Unit.KG, Unit.KG, Unit.KG, "2", "3", "2", "3"),
            (Unit.KG, Unit.G, Unit.G, "500", "150", "0.5", "150000"),
            (Unit.G, Unit.KG, Unit.KG, "0.5", "10", "500", "0.01"),
            (Unit.L, Unit.L, Unit.L, "2", "3", "2", "3"),
            (Unit.L, Unit.ML, Unit.ML, "250", "7", "0.25", "7000"),
            (Unit.ML, Unit.L, Unit.L, "0.5", "1000", "500", "1"),
            (Unit.PC, Unit.PC, Unit.PC, "3", "4", "3", "4"),
        )
        for index, (canonical, input_unit, cost_unit, amount, cost, expected_qty, expected_cost) in enumerate(cases):
            with self.subTest(canonical=canonical, input_unit=input_unit):
                # Every case models an independent stock position. Reuse of the
                # same StockKey would correctly retain the preceding balance.
                self.stocks.rows.clear()
                self.stocks.saved.clear()
                self.movements.rows.clear()
                self.movements.saved.clear()
                self.ingredients.rows[20] = Ingredient(20, 1, "Item", canonical)
                result = self.receive.execute(
                    self.receive_command(
                        quantity_amount=Decimal(amount),
                        quantity_unit=input_unit.value,
                        unit_cost_amount=Decimal(cost),
                        unit_cost_unit=cost_unit.value,
                        source=self.operation(document_id=400 + index),
                    ),
                    self.context,
                )
                self.assertEqual(
                    result.current_quantity,
                    Quantity(Decimal(expected_qty), canonical),
                )
                self.assertEqual(
                    self.movements.saved[-1].unit_cost,
                    UnitCost(expected_cost),
                )

    def test_converted_receipt_costing_uses_canonical_quantity_and_cost(self) -> None:
        self.receive.execute(
            self.receive_command(
                quantity_amount=Decimal("1"),
                quantity_unit=Unit.KG.value,
                unit_cost_amount=Decimal("100"),
                unit_cost_unit=Unit.KG.value,
                source=self.operation(document_id=601),
            ),
            self.context,
        )
        result = self.receive.execute(
            self.receive_command(
                quantity_amount=Decimal("1000"),
                quantity_unit=Unit.G.value,
                unit_cost_amount=Decimal("1"),
                unit_cost_unit=Unit.G.value,
                source=self.operation(document_id=602),
            ),
            self.context,
        )
        self.assertEqual(result.current_quantity, Quantity(Decimal("2"), Unit.KG))
        self.assertEqual(result.current_average_cost, UnitCost("550"))

    def test_incompatible_purchase_quantity_or_cost_units_are_rejected(self) -> None:
        self.ingredients.rows[20] = Ingredient(20, 1, "Flour", Unit.KG)
        invalid_pairs = (("l", "kg"), ("pc", "kg"), ("pk", "kg"))
        for index, (quantity_unit, cost_unit) in enumerate(invalid_pairs):
            with self.subTest(quantity_unit=quantity_unit, cost_unit=cost_unit):
                with self.assertRaises(IncompatibleUnits):
                    self.receive.execute(
                        self.receive_command(
                            quantity_unit=quantity_unit,
                            unit_cost_unit=cost_unit,
                            source=self.operation(document_id=500 + index),
                        ),
                        self.context,
                    )
        with self.assertRaises(IncompatibleUnits):
            self.receive.execute(
                self.receive_command(
                    quantity_unit=Unit.KG.value,
                    unit_cost_unit=Unit.PK.value,
                    source=self.operation(document_id=510),
                ),
                self.context,
            )

    def test_optional_warehouse_requires_exactly_one_active_default(self) -> None:
        self.warehouses.rows[10] = Warehouse(10, 1, "Main", is_default=True)
        command = self.receive_command(warehouse_id=None)
        self.receive.execute(command, self.context)
        self.assertEqual(self.movements.saved[-1].stock_key.warehouse_id, 10)

        self.warehouses.rows[10] = Warehouse(10, 1, "Main", is_default=False)
        with self.assertRaises(WarehouseConfigurationError):
            self.receive.execute(
                self.receive_command(warehouse_id=None, source=self.operation(document_id=101)),
                self.context,
            )

        self.warehouses.rows[10] = Warehouse(10, 1, "Main", is_default=True)
        self.warehouses.rows[11] = Warehouse(11, 1, "Second", is_default=True)
        with self.assertRaises(WarehouseConfigurationError):
            self.receive.execute(
                self.receive_command(warehouse_id=None, source=self.operation(document_id=102)),
                self.context,
            )

    def test_explicit_inactive_warehouse_is_rejected(self) -> None:
        self.warehouses.rows[10] = Warehouse(10, 1, "Closed", is_active=False)
        with self.assertRaises(InactiveWarehouse):
            self.receive.execute(self.receive_command(), self.context)

    def test_receive_existing_stock_uses_domain_and_business_scoped_ports(self) -> None:
        stock = self.seed_stock("2", "2")
        result = self.receive.execute(
            self.receive_command(quantity_amount=Decimal("2"), unit_cost_amount=Decimal("4")),
            self.context,
        )
        self.assertEqual(result.current_quantity, Quantity(Decimal("4"), Unit.KG))
        self.assertEqual(result.current_average_cost, UnitCost("3"))
        self.assertEqual(stock.average_cost, UnitCost("3"))
        self.assertIn((20, 1), self.ingredients.calls)
        self.assertIn((10, 1), self.warehouses.calls)
        self.assertIn(("get_or_create", 1, 10, 20), self.stocks.calls)

    def test_receive_missing_warehouse_or_ingredient_is_rejected(self) -> None:
        with self.assertRaises(ResourceNotFound):
            self.receive.execute(self.receive_command(warehouse_id=999), self.context)
        with self.assertRaises(ResourceNotFound):
            self.receive.execute(self.receive_command(ingredient_id=999), self.context)
        self.assertEqual(self.unit_of_work.committed, 0)

    def test_cross_business_resources_cannot_be_combined(self) -> None:
        self.warehouses.rows[10] = Warehouse(10, 2, "Foreign")
        with self.assertRaises(ResourceNotFound):
            self.receive.execute(self.receive_command(), self.context)

    def test_application_rejects_out_of_scope_repository_result(self) -> None:
        self.warehouses.get_by_id_for_business = lambda _id, _business: Warehouse(
            10, 2, "Out of scope"
        )
        with self.assertRaises(TenantMismatch):
            self.receive.execute(self.receive_command(), self.context)

    def test_receive_duplicate_same_payload_returns_idempotent_result(self) -> None:
        first = self.receive.execute(self.receive_command(), self.context)
        duplicate = self.receive.execute(self.receive_command(), self.context)
        self.assertFalse(first.idempotent)
        self.assertTrue(duplicate.idempotent)
        self.assertEqual(len(self.movements.rows), 1)
        self.assertEqual(duplicate.current_quantity, first.current_quantity)

    def test_receive_same_identity_with_different_payload_conflicts(self) -> None:
        self.receive.execute(self.receive_command(), self.context)
        with self.assertRaises(OperationConflict):
            self.receive.execute(
                self.receive_command(quantity_amount=Decimal("5")),
                self.context,
            )
        self.assertEqual(self.unit_of_work.committed, 1)

    def test_receive_domain_failure_rolls_back_and_does_not_save(self) -> None:
        with self.assertRaises(InvalidQuantity):
            self.receive.execute(
                self.receive_command(quantity_amount=Decimal("0")), self.context
            )
        self.assertEqual(self.unit_of_work.committed, 0)
        self.assertEqual(self.unit_of_work.rolled_back, 1)
        self.assertEqual(self.movements.rows, [])

    def test_failure_appending_movement_rolls_back_stock_projection(self) -> None:
        self.movements.fail_on_save = True
        with self.assertRaises(RuntimeError):
            self.receive.execute(self.receive_command(), self.context)
        self.assertEqual(self.unit_of_work.committed, 0)
        self.assertEqual(self.unit_of_work.rolled_back, 1)
        self.assertIsNone(self.stocks.get_for_business(1, 10, 20))
        self.assertEqual(self.movements.rows, [])

    def test_adjustment_in_and_out_forward_actor_and_reason_to_domain(self) -> None:
        stock = self.seed_stock("3", "5")
        inbound = self.adjust.execute(self.adjust_command(), self.context)
        self.assertEqual(inbound.current_average_cost, UnitCost("5"))
        self.assertEqual(self.movements.saved[-1].actor_id, 77)
        self.assertEqual(self.movements.saved[-1].reason, "Physical count")
        outbound = self.adjust.execute(
            self.adjust_command(
                quantity=Quantity(Decimal("1"), Unit.KG),
                direction=MovementDirection.OUT,
                source=self.operation("inventory_adjustment", 200, 2, "adjust_stock"),
            ),
            self.context,
        )
        self.assertEqual(outbound.current_quantity, Quantity(Decimal("3"), Unit.KG))
        self.assertEqual(outbound.current_average_cost, UnitCost("5"))
        self.assertEqual(stock.quantity, Quantity(Decimal("3"), Unit.KG))
        self.assertEqual(len(self.movements.saved), 2)

    def test_adjustment_requires_actor_and_does_not_accept_unit_cost(self) -> None:
        self.seed_stock("2", "3")
        with self.assertRaises(InvalidApplicationContext):
            self.adjust.execute(self.adjust_command(), InventoryExecutionContext(1))
        with self.assertRaises(TypeError):
            AdjustStockCommand(
                10, 20, Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                "Count", self.operation(), unit_cost=UnitCost("9"),
            )

    def test_adjustment_domain_error_propagates_without_commit(self) -> None:
        self.seed_stock("0", "0")
        with self.assertRaises(NegativeStock):
            self.adjust.execute(
                self.adjust_command(direction=MovementDirection.OUT), self.context
            )
        self.assertEqual(self.unit_of_work.committed, 0)
        self.assertEqual(len(self.movements.rows), 0)

    def test_reversal_builds_context_from_repository_and_appends_new_movement(self) -> None:
        self.seed_stock("0", "0")
        received = self.receive.execute(self.receive_command(), self.context)
        original = self.movements.rows[0]
        original_snapshot = (
            original.quantity,
            original.unit_cost,
            original.balance_after,
            original.average_cost_before,
            original.source_identity,
        )
        result = self.reverse.execute(self.reverse_command(original), self.context)
        reversal = self.movements.rows[-1]
        self.assertFalse(result.idempotent)
        self.assertEqual(reversal.movement_type, MovementType.REVERSAL)
        self.assertEqual(reversal.reverses, original.source_identity)
        self.assertEqual(result.current_quantity, Quantity.zero(Unit.KG))
        self.assertEqual(self.unit_of_work.committed, 2)
        self.assertEqual(original.balance_after, received.current_quantity)
        self.assertEqual(
            (
                original.quantity,
                original.unit_cost,
                original.balance_after,
                original.average_cost_before,
                original.source_identity,
            ),
            original_snapshot,
        )
        self.assertTrue(any(call[0] == "latest" for call in self.movements.calls))
        self.assertTrue(any(call[0] == "has_reversal" for call in self.movements.calls))

    def test_reversal_retry_is_idempotent_but_conflicting_identity_conflicts(self) -> None:
        self.receive.execute(self.receive_command(), self.context)
        original = self.movements.rows[0]
        command = self.reverse_command(original)
        self.reverse.execute(command, self.context)
        duplicate = self.reverse.execute(command, self.context)
        self.assertTrue(duplicate.idempotent)
        self.assertEqual(len(self.movements.rows), 2)
        conflicting = self.reverse_command(original, reason="Different reason")
        with self.assertRaises(OperationConflict):
            self.reverse.execute(conflicting, self.context)

    def test_older_and_already_reversed_movements_are_rejected_from_trusted_facts(self) -> None:
        self.receive.execute(self.receive_command(), self.context)
        first = self.movements.rows[-1]
        self.receive.execute(
            self.receive_command(
                quantity_amount=Decimal("1"),
                quantity_unit=Unit.KG.value,
                source=self.operation(document_id=101),
            ),
            self.context,
        )
        with self.assertRaises(MovementNotReversible):
            self.reverse.execute(self.reverse_command(first), self.context)

        latest = self.movements.rows[-1]
        self.reverse.execute(self.reverse_command(latest), self.context)
        with self.assertRaises(MovementAlreadyReversed):
            self.reverse.execute(
                self.reverse_command(
                    latest,
                    source=self.operation("inventory_reversal", 301, 1, "reverse_movement"),
                ),
                self.context,
            )

    def test_projection_mismatch_rejects_reversal_without_commit(self) -> None:
        stock = self.seed_stock("0", "0")
        self.receive.execute(self.receive_command(), self.context)
        original = self.movements.rows[-1]
        stock.adjust(
            Quantity(Decimal("1"), Unit.KG),
            MovementDirection.OUT,
            SourceIdentity(1, "manual", 500, 1, "test"),
            self.warehouses.rows[10],
            reason="test",
            actor_id=77,
        )
        with self.assertRaises(StockProjectionConflict):
            self.reverse.execute(self.reverse_command(original), self.context)
        self.assertEqual(self.unit_of_work.rolled_back, 1)

    def test_reversal_operation_failure_rolls_back_projection_and_ledger(self) -> None:
        self.receive.execute(self.receive_command(), self.context)
        original = self.movements.rows[-1]
        self.movements.fail_on_save = True
        before_quantity = self.stocks.get_for_business(1, 10, 20).quantity
        with self.assertRaises(RuntimeError):
            self.reverse.execute(self.reverse_command(original), self.context)
        self.assertEqual(self.stocks.get_for_business(1, 10, 20).quantity, before_quantity)
        self.assertEqual(len(self.movements.rows), 1)
        self.assertEqual(self.unit_of_work.rolled_back, 1)

    def test_client_command_contains_no_trusted_reversal_facts(self) -> None:
        command = ReverseStockMovementCommand(
            self.operation(), self.operation("reversal", 2, 1, "reverse")
        )
        self.assertFalse(hasattr(command, "is_latest"))
        self.assertFalse(hasattr(command, "already_reversed"))
        with self.assertRaises(TypeError):
            ReverseStockMovementCommand(
                self.operation(), self.operation("reversal", 2, 1, "reverse"),
                is_latest=True,
            )

    def test_context_is_immutable_and_business_is_validated(self) -> None:
        with self.assertRaises(InvalidApplicationContext):
            InventoryExecutionContext(0)
        with self.assertRaises(AttributeError):
            self.context.business_id = 2
