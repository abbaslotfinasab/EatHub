from decimal import Decimal, localcontext
from unittest import TestCase

from inventory.domain.exceptions import (
    IncompatibleUnits,
    InvalidQuantity,
    InvalidSourceIdentity,
    InvalidStockKey,
    InvalidUnitCost,
)
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.reversal_context import ReversalContext
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit import Unit
from inventory.domain.value_objects.unit_cost import UnitCost


class QuantityTests(TestCase):
    def test_accepts_decimal_compatible_exact_inputs(self) -> None:
        self.assertEqual(Quantity("1.25", Unit.KG).amount, Decimal("1.25"))
        self.assertEqual(Quantity(2, Unit.PC).amount, Decimal("2"))

    def test_rejects_negative_non_finite_and_float_values(self) -> None:
        for amount in (Decimal("-0.1"), Decimal("NaN"), float("1.2")):
            with self.subTest(amount=amount), self.assertRaises(InvalidQuantity):
                Quantity(amount, Unit.KG)

    def test_quantity_precision_matches_v1_bounds(self) -> None:
        self.assertEqual(
            Quantity(Decimal("1.0000000000000"), Unit.KG).amount,
            Decimal("1.0000000000000"),
        )
        for amount in (
            Decimal("0.0000000000001"),
            Decimal("1000000000000000000000000"),
        ):
            with self.subTest(amount=amount), self.assertRaises(InvalidQuantity):
                Quantity(amount, Unit.KG)

    def test_converts_mass_both_directions(self) -> None:
        self.assertEqual(
            Quantity(Decimal("1.25"), Unit.KG).convert_to(Unit.G),
            Quantity(Decimal("1250.00"), Unit.G),
        )
        self.assertEqual(
            Quantity(Decimal("250"), Unit.G).convert_to(Unit.KG),
            Quantity(Decimal("0.250"), Unit.KG),
        )

    def test_converts_volume_both_directions(self) -> None:
        self.assertEqual(
            Quantity(Decimal("2"), Unit.L).convert_to(Unit.ML),
            Quantity(Decimal("2000"), Unit.ML),
        )
        self.assertEqual(
            Quantity(Decimal("125"), Unit.ML).convert_to(Unit.L),
            Quantity(Decimal("0.125"), Unit.L),
        )

    def test_rejects_incompatible_and_unsupported_units(self) -> None:
        for target in (Unit.ML, Unit.PC, Unit.PK):
            with self.subTest(target=target), self.assertRaises(IncompatibleUnits):
                Quantity(Decimal("1"), Unit.KG).convert_to(target)
        with self.assertRaises(IncompatibleUnits):
            Quantity(Decimal("1"), Unit.PC).convert_to(Unit.PK)
        with self.assertRaises(IncompatibleUnits):
            Quantity(Decimal("1"), Unit.PK).convert_to(Unit.PC)

    def test_arithmetic_normalizes_to_left_hand_unit(self) -> None:
        result = Quantity(Decimal("1"), Unit.KG) + Quantity(Decimal("250"), Unit.G)
        self.assertEqual(result, Quantity(Decimal("1.250"), Unit.KG))

    def test_subtraction_rejects_negative_result(self) -> None:
        with self.assertRaises(InvalidQuantity):
            Quantity(Decimal("1"), Unit.KG) - Quantity(Decimal("1500"), Unit.G)

    def test_value_object_is_immutable_and_compares_by_value(self) -> None:
        quantity = Quantity(Decimal("1"), Unit.KG)
        self.assertEqual(quantity, Quantity(Decimal("1"), Unit.KG))
        with self.assertRaises(AttributeError):
            quantity.amount = Decimal("2")

    def test_conversion_and_addition_ignore_ambient_decimal_precision(self) -> None:
        with localcontext() as context:
            context.prec = 2
            converted = Quantity(Decimal("1.234567"), Unit.KG).convert_to(Unit.G)
            total = Quantity(Decimal("1.234567"), Unit.KG) + Quantity(
                Decimal("1"), Unit.G
            )
        self.assertEqual(converted.amount, Decimal("1234.567000"))
        self.assertEqual(total.amount, Decimal("1.235567"))


class OtherValueObjectTests(TestCase):
    def test_unit_cost_is_decimal_based_and_non_negative(self) -> None:
        self.assertEqual(UnitCost("4.125").amount, Decimal("4.125"))
        for amount in (Decimal("-1"), Decimal("Infinity"), 1.25):
            with self.subTest(amount=amount), self.assertRaises(InvalidUnitCost):
                UnitCost(amount)

    def test_unit_cost_precision_matches_v1_bounds(self) -> None:
        max_scale_cost = Decimal("1." + "1" * 48)
        self.assertEqual(UnitCost(max_scale_cost).amount, max_scale_cost)
        for amount in (
            Decimal("1." + "1" * 49),
            Decimal("1" + "0" * 22),
        ):
            with self.subTest(amount=amount), self.assertRaises(InvalidUnitCost):
                UnitCost(amount)

    def test_stock_key_has_deterministic_value_equality(self) -> None:
        first = StockKey(1, 2, 3)
        self.assertEqual(first, StockKey(1, 2, 3))
        self.assertNotEqual(first, StockKey(1, 2, 4))
        with self.assertRaises(InvalidStockKey):
            StockKey(0, 2, 3)
        with self.assertRaises(AttributeError):
            first.warehouse_id = 4

    def test_unit_cost_is_immutable_and_compares_by_value(self) -> None:
        cost = UnitCost("4.25")
        self.assertEqual(cost, UnitCost(Decimal("4.25")))
        with self.assertRaises(AttributeError):
            cost.amount = Decimal("5")

    def test_source_identity_is_immutable_and_compares_by_value(self) -> None:
        first = SourceIdentity(1, "purchase_goods_receipt", 10, 11, "receive_stock")
        self.assertEqual(
            first,
            SourceIdentity(1, "purchase_goods_receipt", 10, 11, "receive_stock"),
        )
        with self.assertRaises(AttributeError):
            first.operation_kind = "other"
        with self.assertRaises(InvalidSourceIdentity):
            SourceIdentity(1, "", 10, 11, "receive_stock")

    def test_reversal_context_is_immutable_and_carries_application_facts(self) -> None:
        identity = SourceIdentity(1, "purchase_goods_receipt", 10, 11, "receive_stock")
        context = ReversalContext(identity, False)
        self.assertEqual(context, ReversalContext(identity, False))
        with self.assertRaises(AttributeError):
            context.already_reversed = True
