from dataclasses import dataclass
from decimal import Decimal, localcontext

from inventory.domain.exceptions import InvalidQuantity, InvalidUnit
from inventory.domain.value_objects.decimal_precision import validate_quantity_precision
from inventory.domain.value_objects.unit import Unit


def as_decimal(value: Decimal | int | str) -> Decimal:
    """Convert an exact V1 quantity; floats and out-of-range values are rejected.

    V1 permits at most 24 integer and 12 fractional digits. Extra trailing
    zeroes do not increase a value's effective scale.
    """
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidQuantity("Quantity values must not be supplied as floats.")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, str)):
        try:
            result = Decimal(value)
        except (ValueError, ArithmeticError) as error:
            raise InvalidQuantity("Quantity must be Decimal-compatible.") from error
    else:
        raise InvalidQuantity("Quantity must be Decimal-compatible.")

    if not result.is_finite():
        raise InvalidQuantity("Quantity must be finite.")
    validate_quantity_precision(result)
    return result


def _precision_for_addition(left: Decimal, right: Decimal) -> int:
    lowest_exponent = min(left.as_tuple().exponent, right.as_tuple().exponent)
    highest_adjusted = max(left.adjusted(), right.adjusted())
    return max(28, highest_adjusted - lowest_exponent + 2)


@dataclass(frozen=True, slots=True)
class Quantity:
    amount: Decimal
    unit: Unit

    def __post_init__(self) -> None:
        amount = as_decimal(self.amount)
        if amount < 0:
            raise InvalidQuantity("Quantity cannot be negative.")
        if not isinstance(self.unit, Unit):
            raise InvalidUnit("Quantity requires a supported Unit.")
        object.__setattr__(self, "amount", amount)

    @classmethod
    def zero(cls, unit: Unit) -> "Quantity":
        return cls(Decimal("0"), unit)

    def convert_to(self, target: Unit) -> "Quantity":
        return Quantity(self.unit.convert_amount_to(self.amount, target), target)

    def __add__(self, other: "Quantity") -> "Quantity":
        converted = self._compatible(other)
        with localcontext() as context:
            context.prec = _precision_for_addition(self.amount, converted.amount)
            result = self.amount + converted.amount
        return Quantity(result, self.unit)

    def __sub__(self, other: "Quantity") -> "Quantity":
        converted = self._compatible(other)
        with localcontext() as context:
            context.prec = _precision_for_addition(self.amount, converted.amount)
            result = self.amount - converted.amount
        if result < 0:
            raise InvalidQuantity("Quantity subtraction cannot be negative.")
        return Quantity(result, self.unit)

    def _compatible(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise InvalidQuantity("Quantity arithmetic requires another Quantity.")
        return other.convert_to(self.unit)
