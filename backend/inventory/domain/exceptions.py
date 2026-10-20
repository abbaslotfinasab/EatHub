"""Business rule violations raised by the Inventory domain."""


class InventoryDomainError(Exception):
    """Base exception for Inventory domain rule violations."""


class InvalidQuantity(InventoryDomainError):
    """A quantity is not a finite, non-negative Decimal value."""


class InvalidUnit(InventoryDomainError):
    """A unit is missing or is not supported by Inventory."""


class IncompatibleUnits(InvalidUnit):
    """Two units cannot be converted between their dimensions."""


class InvalidUnitCost(InventoryDomainError):
    """A unit cost is not a finite, non-negative Decimal value."""


class InvalidStockKey(InventoryDomainError):
    """A stock position has an invalid identity."""


class InvalidIngredient(InventoryDomainError):
    """An Ingredient violates its domain rules."""


class InvalidWarehouse(InventoryDomainError):
    """A Warehouse violates its domain rules."""


class InvalidSourceIdentity(InventoryDomainError):
    """An external operation identity is incomplete or invalid."""


class NegativeStock(InventoryDomainError):
    """A stock operation would make the balance negative."""


class MovementNotReversible(InventoryDomainError):
    """A movement is not the latest effective movement on its Stock position."""


class MovementAlreadyReversed(InventoryDomainError):
    """A movement has already been reversed."""


class InvalidMovement(InventoryDomainError):
    """A movement violates its type, direction, or source rules."""


class InactiveWarehouse(InventoryDomainError):
    """An inactive warehouse cannot receive ordinary inbound stock."""


class TenantMismatch(InventoryDomainError):
    """Related domain objects do not belong to the same Business."""


class InvalidRecipe(InventoryDomainError):
    """A Recipe or one of its lines violates a domain invariant."""
