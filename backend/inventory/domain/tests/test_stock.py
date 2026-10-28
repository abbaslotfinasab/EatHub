from decimal import Decimal, ROUND_DOWN, localcontext
from datetime import datetime, timezone
from unittest import TestCase

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.enums.ingredient import IngredientPreparationLevel
from inventory.domain.enums.movement import MovementDirection, MovementType
from inventory.domain.exceptions import (
    InactiveWarehouse,
    InvalidMovement,
    InvalidQuantity,
    InvalidUnitCost,
    MovementAlreadyReversed,
    MovementNotReversible,
    NegativeStock,
    TenantMismatch,
)
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.reversal_context import ReversalContext
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


class StockTests(TestCase):
    def setUp(self) -> None:
        self.warehouse = Warehouse(10, 1, "Main", is_default=True)
        self.ingredient = Ingredient(
            20, 1, "Flour", Unit.KG, IngredientPreparationLevel.RAW
        )
        self.stock = Stock(self.warehouse, self.ingredient)

    def source(self, line_id: int = 1) -> SourceIdentity:
        return SourceIdentity(1, "purchase_goods_receipt", 100, line_id, "receive_stock")

    def adjustment_source(self, line_id: int = 1) -> SourceIdentity:
        return SourceIdentity(1, "inventory_adjustment", 200, line_id, "adjust_stock")

    def reversal_source(self, line_id: int = 1) -> SourceIdentity:
        return SourceIdentity(1, "inventory_reversal", 300, line_id, "reverse_movement")

    def test_stock_starts_at_zero_and_receipt_into_zero_uses_cost(self) -> None:
        self.assertEqual(self.stock.quantity, Quantity.zero(Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost.zero())
        movement = self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("5"), self.source(), self.warehouse
        )
        self.assertEqual(self.stock.quantity, Quantity(Decimal("10"), Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost("5"))
        self.assertEqual(movement.balance_after, self.stock.quantity)

    def test_opening_balance_initializes_only_an_empty_position(self) -> None:
        movement = self.stock.open_balance(
            Quantity("2.5", Unit.KG), UnitCost("3.25"),
            SourceIdentity(1, "inventory_opening_stock", 500, 1, "post"),
            self.warehouse, actor_id=99,
        )
        self.assertEqual(movement.movement_type, MovementType.OPENING_BALANCE)
        self.assertEqual(movement.direction, MovementDirection.IN)
        self.assertEqual(self.stock.quantity, Quantity("2.5", Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost("3.25"))
        with self.assertRaises(InvalidMovement):
            self.stock.open_balance(
                Quantity("1", Unit.KG), UnitCost("3"),
                SourceIdentity(1, "inventory_opening_stock", 501, 1, "post"),
                self.warehouse, actor_id=99,
            )

    def test_weighted_average_receipt_and_multiple_costs(self) -> None:
        self.stock.receive(
            Quantity(Decimal("20"), Unit.KG), UnitCost("4"), self.source(1), self.warehouse
        )
        self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("5"), self.source(2), self.warehouse
        )
        self.assertEqual(self.stock.quantity, Quantity(Decimal("30"), Unit.KG))
        self.assertEqual(
            self.stock.average_cost.amount,
            Decimal("4." + "3" * 48),
        )
        self.assertIsInstance(self.stock.average_cost.amount, Decimal)

    def test_receipt_normalizes_quantity_to_canonical_unit(self) -> None:
        movement = self.stock.receive(
            Quantity(Decimal("10000"), Unit.G), UnitCost("2"), self.source(), self.warehouse
        )
        self.assertEqual(movement.quantity, Quantity(Decimal("10.000"), Unit.KG))
        self.assertEqual(self.stock.quantity, movement.balance_after)

    def test_zero_cost_receipt_is_supported(self) -> None:
        movement = self.stock.receive(
            Quantity(Decimal("2"), Unit.KG), UnitCost.zero(), self.source(), self.warehouse
        )
        self.assertEqual(movement.unit_cost, UnitCost.zero())
        self.assertEqual(self.stock.average_cost, UnitCost.zero())

    def test_outbound_preserves_average_cost_and_zero_balance_resets_it(self) -> None:
        self.stock.receive(
            Quantity(Decimal("5"), Unit.KG), UnitCost("3"), self.source(), self.warehouse
        )
        self.stock.adjust(
            Quantity(Decimal("2"), Unit.KG), MovementDirection.OUT,
            self.adjustment_source(), self.warehouse, reason="Count", actor_id=99,
        )
        self.assertEqual(self.stock.average_cost, UnitCost("3"))
        self.stock.adjust(
            Quantity(Decimal("3"), Unit.KG), MovementDirection.OUT,
            self.adjustment_source(2), self.warehouse, reason="Count", actor_id=99,
        )
        self.assertEqual(self.stock.quantity, Quantity.zero(Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost.zero())

    def test_adjustment_in_and_out_use_current_average_cost(self) -> None:
        self.stock.receive(
            Quantity(Decimal("5"), Unit.KG), UnitCost("3"), self.source(), self.warehouse
        )
        inbound = self.stock.adjust(
            Quantity(Decimal("2"), Unit.KG), MovementDirection.IN,
            self.adjustment_source(), self.warehouse, reason="Physical count", actor_id=99,
        )
        outbound = self.stock.adjust(
            Quantity(Decimal("1"), Unit.KG), MovementDirection.OUT,
            self.adjustment_source(2), self.warehouse, reason="Physical count", actor_id=99,
        )
        self.assertEqual(inbound.unit_cost, UnitCost("3"))
        self.assertEqual(outbound.unit_cost, UnitCost("3"))
        self.assertEqual(self.stock.average_cost, UnitCost("3"))

    def test_adjustment_requires_reason_actor_and_source_identity(self) -> None:
        with self.assertRaises(InvalidMovement):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                self.adjustment_source(), self.warehouse, reason=" ", actor_id=99,
            )
        with self.assertRaises(InvalidMovement):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                self.adjustment_source(), self.warehouse, reason="Count", actor_id=0,
            )
        with self.assertRaises(InvalidMovement):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                self.adjustment_source(), self.warehouse, reason="Count", actor_id=None,
            )
        with self.assertRaises(TenantMismatch):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                SourceIdentity(2, "inventory_adjustment", 200, 1, "adjust_stock"),
                self.warehouse, reason="Count", actor_id=99,
            )
        # Actor identity is accepted as audit data; Domain performs no authorization.
        movement = self.stock.adjust(
            Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
            self.adjustment_source(), self.warehouse, reason="Count", actor_id=99,
        )
        self.assertEqual(movement.actor_id, 99)

    def test_adjustment_contract_does_not_accept_arbitrary_cost(self) -> None:
        with self.assertRaises(TypeError):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.IN,
                self.adjustment_source(), self.warehouse, reason="Count", actor_id=99,
                unit_cost=UnitCost("8"),
            )

    def test_outbound_cannot_make_stock_negative(self) -> None:
        with self.assertRaises(NegativeStock):
            self.stock.adjust(
                Quantity(Decimal("1"), Unit.KG), MovementDirection.OUT,
                self.adjustment_source(), self.warehouse, reason="Count", actor_id=99,
            )
        self.assertEqual(self.stock.quantity, Quantity.zero(Unit.KG))

    def test_movement_quantity_must_be_positive(self) -> None:
        with self.assertRaises(InvalidQuantity):
            self.stock.receive(
                Quantity.zero(Unit.KG), UnitCost("1"), self.source(), self.warehouse
            )
        self.assertEqual(self.stock.quantity, Quantity.zero(Unit.KG))

    def test_inactive_warehouse_cannot_receive(self) -> None:
        inactive = Warehouse(10, 1, "Main", is_active=False)
        with self.assertRaises(InactiveWarehouse):
            self.stock.receive(
                Quantity(Decimal("1"), Unit.KG), UnitCost("2"), self.source(), inactive
            )

    def test_stock_requires_same_business_warehouse_and_ingredient(self) -> None:
        with self.assertRaises(TenantMismatch):
            Stock(self.warehouse, Ingredient(21, 2, "Rice", Unit.KG))
        with self.assertRaises(TenantMismatch):
            self.stock.receive(
                Quantity(Decimal("1"), Unit.KG), UnitCost("1"),
                SourceIdentity(2, "purchase", 1, 1, "receive"), self.warehouse,
            )

    def test_transition_rejects_warehouse_from_another_position(self) -> None:
        with self.assertRaises(TenantMismatch):
            self.stock.receive(
                Quantity(Decimal("1"), Unit.KG), UnitCost("1"), self.source(),
                Warehouse(11, 1, "Other"),
            )

    def test_movement_type_direction_semantics_are_separate(self) -> None:
        for movement_type, direction in (
            (MovementType.RECEIPT, MovementDirection.IN),
            (MovementType.ADJUSTMENT, MovementDirection.IN),
            (MovementType.ADJUSTMENT, MovementDirection.OUT),
            (MovementType.REVERSAL, MovementDirection.IN),
            (MovementType.REVERSAL, MovementDirection.OUT),
        ):
            StockMovement.validate_semantics(movement_type, direction)
        with self.assertRaises(InvalidMovement):
            StockMovement.validate_semantics(MovementType.RECEIPT, MovementDirection.OUT)

    def test_movement_snapshot_is_immutable_and_caller_cannot_supply_it(self) -> None:
        movement = self.stock.receive(
            Quantity(Decimal("1"), Unit.KG), UnitCost("2"), self.source(), self.warehouse
        )
        with self.assertRaises(AttributeError):
            movement.balance_after = Quantity(Decimal("999"), Unit.KG)
        with self.assertRaises(AttributeError):
            movement.average_cost_before = UnitCost("999")
        with self.assertRaises(TypeError):
            StockMovement(balance_after=Quantity(Decimal("999"), Unit.KG))

    def test_movement_reconstitution_preserves_exact_historical_state(self) -> None:
        self.stock.receive(
            Quantity(Decimal("3.000001"), Unit.KG),
            UnitCost("2.123456"),
            self.source(1),
            self.warehouse,
        )
        original = self.stock.receive(
            Quantity(Decimal("0.000002"), Unit.KG),
            UnitCost("8.000009"),
            self.source(2),
            self.warehouse,
            occurred_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        stock_state = (self.stock.quantity, self.stock.average_cost)

        restored = StockMovement.reconstitute(
            stock_key=original.stock_key,
            movement_type=original.movement_type,
            direction=original.direction,
            quantity=original.quantity,
            unit_cost=original.unit_cost,
            source_identity=original.source_identity,
            balance_after=original.balance_after,
            average_cost_before=original.average_cost_before,
            reason=original.reason,
            actor_id=original.actor_id,
            reverses=original.reverses,
            occurred_at=original.occurred_at,
        )

        self.assertIsNot(restored, original)
        self.assertEqual(restored, original)
        self.assertEqual(restored.quantity.amount, Decimal("0.000002"))
        self.assertEqual(restored.unit_cost.amount, Decimal("8.000009"))
        self.assertEqual(restored.balance_after.amount, Decimal("3.000003"))
        self.assertEqual(restored.average_cost_before.amount, Decimal("2.123456"))
        self.assertEqual(restored.source_identity, original.source_identity)
        self.assertEqual(restored.occurred_at, original.occurred_at)
        self.assertEqual((self.stock.quantity, self.stock.average_cost), stock_state)
        with self.assertRaises(AttributeError):
            restored.balance_after = Quantity(Decimal("99"), Unit.KG)

    def test_movement_reconstitution_preserves_reversal_reference(self) -> None:
        original = self.stock.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("3"),
            self.source(),
            self.warehouse,
        )
        reversal = self.stock.reverse(
            original,
            self.reversal_source(),
            self.warehouse,
            context=ReversalContext(original.source_identity, False),
        )
        restored = StockMovement.reconstitute(
            stock_key=reversal.stock_key,
            movement_type=reversal.movement_type,
            direction=reversal.direction,
            quantity=reversal.quantity,
            unit_cost=reversal.unit_cost,
            source_identity=reversal.source_identity,
            balance_after=reversal.balance_after,
            average_cost_before=reversal.average_cost_before,
            reason=reversal.reason,
            actor_id=reversal.actor_id,
            reverses=reversal.reverses,
            occurred_at=reversal.occurred_at,
        )
        self.assertEqual(restored.reverses, original.source_identity)
        self.assertEqual(restored, reversal)

    def test_movement_reconstitution_rejects_invalid_persisted_state(self) -> None:
        movement = self.stock.receive(
            Quantity(Decimal("1"), Unit.KG),
            UnitCost("2"),
            self.source(),
            self.warehouse,
        )
        with self.assertRaises(InvalidMovement):
            StockMovement.reconstitute(
                stock_key=movement.stock_key,
                movement_type=MovementType.RECEIPT,
                direction=MovementDirection.OUT,
                quantity=movement.quantity,
                unit_cost=movement.unit_cost,
                source_identity=movement.source_identity,
                balance_after=movement.balance_after,
                average_cost_before=movement.average_cost_before,
            )
        with self.assertRaises(InvalidMovement):
            StockMovement.reconstitute(
                stock_key=movement.stock_key,
                movement_type=movement.movement_type,
                direction=movement.direction,
                quantity=Quantity.zero(Unit.KG),
                unit_cost=movement.unit_cost,
                source_identity=movement.source_identity,
                balance_after=movement.balance_after,
                average_cost_before=movement.average_cost_before,
            )

    def test_reverse_latest_inbound_restores_preceding_average(self) -> None:
        self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("4"), self.source(1), self.warehouse
        )
        latest = self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("6"), self.source(2), self.warehouse
        )
        original_state = (latest.quantity, latest.unit_cost, latest.balance_after)
        reversal = self.stock.reverse(
            latest, self.reversal_source(2), self.warehouse,
            context=ReversalContext(latest.source_identity, False),
        )
        self.assertEqual(self.stock.quantity, Quantity(Decimal("10"), Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost("4"))
        self.assertEqual(reversal.direction, MovementDirection.OUT)
        self.assertEqual(reversal.unit_cost, UnitCost("6"))
        self.assertEqual(reversal.reverses, latest.source_identity)
        self.assertEqual((latest.quantity, latest.unit_cost, latest.balance_after), original_state)

    def test_reverse_latest_inbound_restores_average_after_non_terminating_division(self) -> None:
        self.stock.receive(
            Quantity(Decimal("1"), Unit.KG), UnitCost("1"), self.source(1), self.warehouse
        )
        latest = self.stock.receive(
            Quantity(Decimal("2"), Unit.KG), UnitCost("2"), self.source(2), self.warehouse
        )
        self.assertNotEqual(self.stock.average_cost, UnitCost("1"))
        self.stock.reverse(
            latest, self.reversal_source(2), self.warehouse,
            context=ReversalContext(latest.source_identity, False),
        )
        self.assertEqual(self.stock.quantity, Quantity(Decimal("1"), Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost("1"))

    def test_reverse_latest_outbound_restores_quantity_and_average(self) -> None:
        self.stock.receive(
            Quantity(Decimal("5"), Unit.KG), UnitCost("3"), self.source(), self.warehouse
        )
        latest = self.stock.adjust(
            Quantity(Decimal("2"), Unit.KG), MovementDirection.OUT,
            self.adjustment_source(), self.warehouse, reason="Count", actor_id=99,
        )
        self.stock.reverse(
            latest, self.reversal_source(), self.warehouse,
            context=ReversalContext(latest.source_identity, False),
        )
        self.assertEqual(self.stock.quantity, Quantity(Decimal("5"), Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost("3"))

    def test_reverse_latest_movement_to_zero_resets_average_cost(self) -> None:
        latest = self.stock.receive(
            Quantity(Decimal("2"), Unit.KG), UnitCost("8"), self.source(), self.warehouse
        )
        self.stock.reverse(
            latest, self.reversal_source(), self.warehouse,
            context=ReversalContext(latest.source_identity, False),
        )
        self.assertEqual(self.stock.quantity, Quantity.zero(Unit.KG))
        self.assertEqual(self.stock.average_cost, UnitCost.zero())

    def test_rejects_reversal_of_older_movement_after_later_movement(self) -> None:
        older = self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("4"), self.source(1), self.warehouse
        )
        later = self.stock.receive(
            Quantity(Decimal("10"), Unit.KG), UnitCost("6"), self.source(2), self.warehouse
        )
        before = (self.stock.quantity, self.stock.average_cost)
        with self.assertRaises(MovementNotReversible):
            self.stock.reverse(
                older, self.reversal_source(), self.warehouse,
                context=ReversalContext(later.source_identity, False),
            )
        self.assertEqual((self.stock.quantity, self.stock.average_cost), before)

    def test_rejects_repeated_reversal(self) -> None:
        original = self.stock.receive(
            Quantity(Decimal("1"), Unit.KG), UnitCost("2"), self.source(), self.warehouse
        )
        self.stock.reverse(
            original, self.reversal_source(), self.warehouse,
            context=ReversalContext(original.source_identity, False),
        )
        with self.assertRaises(MovementAlreadyReversed):
            self.stock.reverse(
                original, self.reversal_source(2), self.warehouse,
                context=ReversalContext(None, True),
            )

    def test_reversal_requires_context_and_same_stock(self) -> None:
        movement = self.stock.receive(
            Quantity(Decimal("1"), Unit.KG), UnitCost("2"), self.source(), self.warehouse
        )
        with self.assertRaises(InvalidMovement):
            self.stock.reverse(movement, self.reversal_source(), self.warehouse, context=None)
        foreign = Stock(Warehouse(11, 1, "Other"), self.ingredient)
        with self.assertRaises(TenantMismatch):
            foreign.reverse(
                movement, self.reversal_source(), Warehouse(11, 1, "Other"),
                context=ReversalContext(movement.source_identity, False),
            )

    def test_reconstitution_validates_projection_without_public_setters(self) -> None:
        restored = Stock.reconstitute(
            self.warehouse, self.ingredient,
            Quantity(Decimal("4"), Unit.KG), UnitCost("2.5"),
        )
        self.assertEqual(restored.quantity, Quantity(Decimal("4"), Unit.KG))
        self.assertEqual(restored.average_cost, UnitCost("2.5"))
        with self.assertRaises(InvalidUnitCost):
            Stock.reconstitute(
                self.warehouse, self.ingredient, Quantity.zero(Unit.KG), UnitCost("1")
            )
        with self.assertRaises(InvalidQuantity):
            Stock.reconstitute(
                self.warehouse, self.ingredient,
                Quantity(Decimal("1"), Unit.G), UnitCost("1"),
            )
        with self.assertRaises(AttributeError):
            restored.quantity = Quantity.zero(Unit.KG)

    def test_avco_is_decimal_and_deterministic_under_decimal_context(self) -> None:
        def calculate() -> UnitCost:
            stock = Stock(self.warehouse, self.ingredient)
            stock.receive(
                Quantity(Decimal("1"), Unit.KG),
                UnitCost("1"),
                self.source(1),
                self.warehouse,
            )
            with localcontext() as context:
                context.prec = 2
                context.rounding = ROUND_DOWN
                stock.receive(
                    Quantity(Decimal("2"), Unit.KG),
                    UnitCost("2"),
                    self.source(2),
                    self.warehouse,
                )
            return stock.average_cost

        first = calculate()
        self.assertEqual(first, UnitCost(Decimal("1." + "6" * 47 + "7")))
        self.assertIsInstance(first.amount, Decimal)
        self.assertEqual(first, calculate())

    def test_avco_uses_bounded_half_even_scale_and_reversal_restores_exact_prior_cost(
        self,
    ) -> None:
        precise_cost = Decimal("4." + "1234567890" * 4 + "12345678")
        self.assertEqual(-precise_cost.as_tuple().exponent, 48)
        self.stock.receive(
            Quantity(Decimal("1.123456789012"), Unit.KG),
            UnitCost(precise_cost),
            self.source(1),
            self.warehouse,
        )
        prior_average = self.stock.average_cost
        latest = self.stock.receive(
            Quantity(Decimal("2"), Unit.KG),
            UnitCost("7"),
            self.source(2),
            self.warehouse,
        )
        self.assertEqual(self.stock.average_cost.amount.as_tuple().exponent, -48)

        self.stock.reverse(
            latest,
            self.reversal_source(2),
            self.warehouse,
            context=ReversalContext(latest.source_identity, False),
        )
        self.assertEqual(self.stock.average_cost, prior_average)
