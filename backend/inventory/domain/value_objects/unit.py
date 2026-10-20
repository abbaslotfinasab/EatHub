from decimal import Decimal, localcontext
from enum import StrEnum

from inventory.domain.exceptions import IncompatibleUnits, InvalidUnit


class Unit(StrEnum):
    KG = "kg"
    G = "g"
    L = "l"
    ML = "ml"
    PC = "pc"
    PK = "pk"

    @property
    def dimension(self) -> str:
        if self in (Unit.KG, Unit.G):
            return "mass"
        if self in (Unit.L, Unit.ML):
            return "volume"
        if self is Unit.PC:
            return "piece"
        return "pack"

    def convert_amount_to(
        self,
        amount: Decimal | int | str,
        target: "Unit",
    ) -> Decimal:
        """Convert a Decimal-compatible amount without passing through float."""
        from inventory.domain.value_objects.quantity import as_decimal

        if not isinstance(target, Unit):
            raise InvalidUnit("Target unit must be a supported Unit.")
        value = as_decimal(amount)
        if self is target:
            return value

        conversions = {
            (Unit.KG, Unit.G): 1000,
            (Unit.G, Unit.KG): "0.001",
            (Unit.L, Unit.ML): 1000,
            (Unit.ML, Unit.L): "0.001",
        }
        factor = conversions.get((self, target))
        if factor is None:
            raise IncompatibleUnits(
                f"Cannot convert {self.value} to {target.value}."
            )
        with localcontext() as context:
            context.prec = max(28, len(value.as_tuple().digits) + 4)
            return value * as_decimal(factor)
