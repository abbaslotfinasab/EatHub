"""Stable application-boundary errors for Inventory use cases."""

from inventory.domain.exceptions import InventoryDomainError as InventoryDomainError


class InventoryApplicationError(Exception):
    """Base class for Inventory application failures."""


class InvalidApplicationContext(InventoryApplicationError):
    """The trusted execution context is invalid."""


class InvalidApplicationInput(InventoryApplicationError):
    """An application command is structurally invalid."""


class ResourceNotFound(InventoryApplicationError):
    """A business-scoped Inventory resource does not exist."""


class WarehouseConfigurationError(InventoryApplicationError):
    """The Business has no unique active default Warehouse for this operation."""


class OperationConflict(InventoryApplicationError):
    """A source identity is already associated with different operation data."""


class StockProjectionConflict(InventoryApplicationError):
    """Persisted Stock does not match the target movement's resulting balance."""
