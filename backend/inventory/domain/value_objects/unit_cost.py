from dataclasses import dataclass
from decimal import Decimal

from inventory.domain.value_objects.decimal_precision import validate_cost_precision
from inventory.domain.exceptions import InvalidUnitCost


@dataclass(frozen=True, slots=True)
class UnitCost:
    """Business accounting-currency cost for one canonical Ingredient unit.

    Currency is intentionally not represented here. Callers must provide cost
    for the Ingredient's canonical unit; the Domain never guesses its basis.
    V1 accepts at most 22 integer and 48 fractional digits. AVCO values are
    rounded to 48 fractional digits using ROUND_HALF_EVEN in the Domain.
    """

    amount: Decimal | int | str

    def __post_init__(self) -> None:
        value = self.amount
        if isinstance(value, (float, bool)):
            raise InvalidUnitCost("Unit cost must not be supplied as a float.")
        if not isinstance(value, Decimal):
            if not isinstance(value, (int, str)):
                raise InvalidUnitCost("Unit cost must be Decimal-compatible.")
            try:
                value = Decimal(value)
            except (ValueError, ArithmeticError) as error:
                raise InvalidUnitCost(
                    "Unit cost must be Decimal-compatible."
                ) from error
        if not value.is_finite() or value < 0:
            raise InvalidUnitCost("Unit cost must be finite and non-negative.")
        validate_cost_precision(value)
        object.__setattr__(self, "amount", value)

    @classmethod
    def zero(cls) -> "UnitCost":
        return cls(Decimal("0"))
