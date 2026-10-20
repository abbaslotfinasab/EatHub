from typing import Protocol

from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.application.dto.stock_balance import (
    ListStockBalancesQuery,
    StockBalancePageDTO,
)


class IngredientRepository(Protocol):
    def get_by_id_for_business(
        self, ingredient_id: int, business_id: int
    ) -> Ingredient | None:
        """Load an Ingredient only when it belongs to the requested Business."""


class WarehouseRepository(Protocol):
    def get_by_id_for_business(
        self, warehouse_id: int, business_id: int
    ) -> Warehouse | None:
        """Load a Warehouse only when it belongs to the requested Business."""

    def get_active_defaults_for_business(self, business_id: int) -> list[Warehouse]:
        """Return active defaults scoped to a Business."""


class StockRepository(Protocol):
    def get_for_business(
        self,
        business_id: int,
        warehouse_id: int,
        ingredient_id: int,
    ) -> Stock | None:
        """Load the business-scoped Stock projection, if it exists."""

    def get_or_create_for_business(
        self,
        business_id: int,
        warehouse: Warehouse,
        ingredient: Ingredient,
    ) -> Stock:
        """Return the business-scoped Stock projection, creating it if absent."""

    def save(self, stock: Stock) -> None:
        """Persist the projection in the current Unit of Work."""


class StockBalanceRepository(Protocol):
    def list_for_business(
        self, query: ListStockBalancesQuery
    ) -> StockBalancePageDTO:
        """Return one bounded page of V1 balances for a Business."""


class StockMovementRepository(Protocol):
    def find_by_source_identity_for_business(
        self,
        business_id: int,
        source_identity: SourceIdentity,
    ) -> StockMovement | None:
        """Find a movement by its operation identity within one Business."""

    def get_latest_effective_for_stock(
        self,
        business_id: int,
        stock_key: StockKey,
    ) -> StockMovement | None:
        """Return the latest effective movement for this business-scoped Stock."""

    def has_reversal_for_source(
        self,
        business_id: int,
        original_source_identity: SourceIdentity,
    ) -> bool:
        """Return whether the original movement already has a reversal."""

    def save(self, movement: StockMovement) -> None:
        """Append an immutable movement in the current Unit of Work.

        Infrastructure must enforce unique ``(business_id, source_identity)``
        and translate a conflicting identity into ``OperationConflict``. The
        preflight lookup is not a concurrency guarantee.
        """
