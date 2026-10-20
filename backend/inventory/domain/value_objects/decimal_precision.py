"""Finite Decimal bounds for Inventory V1 Domain values.

These limits define V1 quantity and cost semantics independently of Django.
They match the exact numeric ranges persisted by the V1 schema.
"""

from decimal import Decimal
from typing import Type

from inventory.domain.exceptions import InvalidQuantity, InvalidUnitCost


QUANTITY_MAX_INTEGER_DIGITS = 24
QUANTITY_MAX_SCALE = 12
COST_MAX_INTEGER_DIGITS = 22
COST_MAX_SCALE = 48


def validate_quantity_precision(value: Decimal) -> None:
    _validate_precision(
        value,
        max_integer_digits=QUANTITY_MAX_INTEGER_DIGITS,
        max_scale=QUANTITY_MAX_SCALE,
        error_type=InvalidQuantity,
        label="Quantity",
    )


def validate_cost_precision(value: Decimal) -> None:
    _validate_precision(
        value,
        max_integer_digits=COST_MAX_INTEGER_DIGITS,
        max_scale=COST_MAX_SCALE,
        error_type=InvalidUnitCost,
        label="UnitCost",
    )


def _validate_precision(
    value: Decimal,
    *,
    max_integer_digits: int,
    max_scale: int,
    error_type: Type[Exception],
    label: str,
) -> None:
    if not value:
        return

    _, digits, exponent = value.as_tuple()
    trailing_zeroes = 0
    for digit in reversed(digits):
        if digit != 0:
            break
        trailing_zeroes += 1

    effective_exponent = exponent + trailing_zeroes
    fractional_places = max(0, -effective_exponent)
    integer_digits = max(value.adjusted() + 1, 0)
    if fractional_places > max_scale or integer_digits > max_integer_digits:
        raise error_type(
            f"{label} exceeds the V1 limit of {max_integer_digits} integer "
            f"digits and {max_scale} fractional digits."
        )
