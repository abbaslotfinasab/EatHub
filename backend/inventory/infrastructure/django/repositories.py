from django.db import IntegrityError, connection, transaction
from django.db.models import QuerySet

from inventory.application.exceptions import OperationConflict, ResourceNotFound
from inventory.application.dto.stock_balance import (
    ListStockBalancesQuery,
    StockBalanceDTO,
    StockBalancePageDTO,
)
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.stock import Stock
from inventory.domain.entities.stock_movement import StockMovement
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.exceptions import InvalidStockKey, TenantMismatch
from inventory.domain.value_objects.source_identity import SourceIdentity
from inventory.domain.value_objects.stock_key import StockKey
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.mappers import (
    ingredient_to_domain,
    movement_to_domain,
    movement_to_orm,
    stock_to_domain,
    stock_to_orm,
    warehouse_to_domain,
)
from inventory.infrastructure.django.models import (
    InventoryV1Stock,
    InventoryV1StockMovement,
)
from inventory.models import Ingredient as LegacyIngredient
from inventory.models import Warehouse as LegacyWarehouse


def _stock_rows(*, lock: bool = False) -> QuerySet:
    rows = InventoryV1Stock.objects.select_related("warehouse", "ingredient")
    if lock and connection.in_atomic_block:
        # Lock only the projection row. Joined Warehouse/Ingredient rows are
        # references, not part of this stock mutation's concurrency boundary.
        rows = rows.select_for_update(of=("self",))
    return rows


def _movement_rows() -> QuerySet:
    return InventoryV1StockMovement.objects.select_related(
        "stock", "stock__warehouse", "stock__ingredient"
    )


class DjangoIngredientRepository:
    def get_by_id_for_business(
        self, ingredient_id: int, business_id: int
    ) -> Ingredient | None:
        row = LegacyIngredient.objects.filter(
            pk=ingredient_id, business_id=business_id
        ).first()
        return ingredient_to_domain(row) if row is not None else None


class DjangoWarehouseRepository:
    def get_by_id_for_business(
        self, warehouse_id: int, business_id: int
    ) -> Warehouse | None:
        row = LegacyWarehouse.objects.filter(
            pk=warehouse_id, business_id=business_id
        ).first()
        return warehouse_to_domain(row) if row is not None else None

    def get_active_defaults_for_business(self, business_id: int) -> list[Warehouse]:
        rows = LegacyWarehouse.objects.filter(
            business_id=business_id, is_active=True, is_default=True
        ).order_by("pk")
        return [warehouse_to_domain(row) for row in rows]


class DjangoStockRepository:
    @staticmethod
    def _require_business_references(
        business_id: int, warehouse_id: int, ingredient_id: int
    ) -> None:
        warehouse_exists = LegacyWarehouse.objects.filter(
            pk=warehouse_id, business_id=business_id
        ).exists()
        ingredient_exists = LegacyIngredient.objects.filter(
            pk=ingredient_id, business_id=business_id
        ).exists()
        if not warehouse_exists or not ingredient_exists:
            raise ResourceNotFound(
                "Stock Warehouse and Ingredient must exist in the requested Business."
            )

    def get_for_business(
        self,
        business_id: int,
        warehouse_id: int,
        ingredient_id: int,
    ) -> Stock | None:
        row = _stock_rows(lock=True).filter(
            business_id=business_id,
            warehouse_id=warehouse_id,
            ingredient_id=ingredient_id,
        ).first()
        return stock_to_domain(row) if row is not None else None

    def get_or_create_for_business(
        self,
        business_id: int,
        warehouse: Warehouse,
        ingredient: Ingredient,
    ) -> Stock:
        if (
            not isinstance(warehouse, Warehouse)
            or not isinstance(ingredient, Ingredient)
            or warehouse.id is None
            or ingredient.id is None
            or business_id != warehouse.business_id
            or business_id != ingredient.business_id
        ):
            raise TenantMismatch("Stock creation requires same-Business identified references.")
        self._require_business_references(
            business_id, warehouse.id, ingredient.id
        )
        # The unique constraint on (business, warehouse, ingredient) resolves
        # simultaneous first-stock creation. Django's get_or_create handles
        # the insert race in a savepoint; the subsequent query locks and
        # reloads the committed/current projection before returning it.
        row, _created = InventoryV1Stock.objects.get_or_create(
            business_id=business_id,
            warehouse_id=warehouse.id,
            ingredient_id=ingredient.id,
            defaults={"unit": ingredient.canonical_unit.value},
        )
        locked = _stock_rows(lock=True).get(
            business_id=business_id,
            warehouse_id=warehouse.id,
            ingredient_id=ingredient.id,
        )
        return stock_to_domain(locked)

    def save(self, stock: Stock) -> None:
        key = stock.key
        self._require_business_references(
            key.business_id, key.warehouse_id, key.ingredient_id
        )
        row = _stock_rows(lock=True).filter(
            business_id=key.business_id,
            warehouse_id=key.warehouse_id,
            ingredient_id=key.ingredient_id,
        ).first()
        if row is not None:
            existing = stock_to_domain(row)
            if existing.key != key:
                raise TenantMismatch("Persisted Stock row does not match its scoped key.")
        if row is None:
            raise ResourceNotFound(
                "Stock must be obtained through the business-scoped creation operation before saving."
            )
        stock_to_orm(stock, row=row).save()


class DjangoStockBalanceRepository:
    """Read-only, bounded queries over the authoritative Inventory V1 projection."""

    def list_for_business(
        self, query: ListStockBalancesQuery
    ) -> StockBalancePageDTO:
        rows = InventoryV1Stock.objects.filter(
            business_id=query.business_id,
            warehouse__business_id=query.business_id,
            ingredient__business_id=query.business_id,
        ).select_related("warehouse", "ingredient")

        if query.ingredient_id is not None:
            rows = rows.filter(ingredient_id=query.ingredient_id)
        if query.warehouse_id is not None:
            rows = rows.filter(warehouse_id=query.warehouse_id)

        count = rows.count()
        offset = (query.page - 1) * query.page_size
        page_rows = rows.order_by("pk")[offset : offset + query.page_size]
        return StockBalancePageDTO(
            count=count,
            page=query.page,
            page_size=query.page_size,
            results=[
                StockBalanceDTO(
                    id=row.pk,
                    ingredient_id=row.ingredient_id,
                    ingredient_name=row.ingredient.name,
                    warehouse_id=row.warehouse_id,
                    warehouse_name=row.warehouse.name,
                    quantity=row.quantity,
                    unit=Unit(row.unit),
                    average_cost=row.average_cost,
                )
                for row in page_rows
            ],
        )


class DjangoStockMovementRepository:
    def find_by_source_identity_for_business(
        self,
        business_id: int,
        source_identity: SourceIdentity,
    ) -> StockMovement | None:
        if source_identity.business_id != business_id:
            raise TenantMismatch("SourceIdentity belongs to another Business.")
        row = _movement_rows().filter(
            business_id=business_id,
            source_type=source_identity.source_type,
            source_document_id=source_identity.source_document_id,
            source_line_id=source_identity.source_line_id,
            operation_kind=source_identity.operation_kind,
        ).first()
        return movement_to_domain(row) if row is not None else None

    def get_latest_effective_for_stock(
        self,
        business_id: int,
        stock_key: StockKey,
    ) -> StockMovement | None:
        if stock_key.business_id != business_id:
            raise TenantMismatch("StockKey belongs to another Business.")
        row = (
            _movement_rows()
            .filter(
                business_id=business_id,
                stock__business_id=business_id,
                stock__warehouse_id=stock_key.warehouse_id,
                stock__ingredient_id=stock_key.ingredient_id,
            )
            .order_by("-pk")
            .first()
        )
        return movement_to_domain(row) if row is not None else None

    def has_reversal_for_source(
        self,
        business_id: int,
        original_source_identity: SourceIdentity,
    ) -> bool:
        if original_source_identity.business_id != business_id:
            raise TenantMismatch("SourceIdentity belongs to another Business.")
        return InventoryV1StockMovement.objects.filter(
            business_id=business_id,
            movement_type="reversal",
            reverses_source_type=original_source_identity.source_type,
            reverses_source_document_id=original_source_identity.source_document_id,
            reverses_source_line_id=original_source_identity.source_line_id,
            reverses_operation_kind=original_source_identity.operation_kind,
        ).exists()

    def save(self, movement: StockMovement) -> None:
        key = movement.stock_key
        stock_row = _stock_rows().filter(
            business_id=key.business_id,
            warehouse_id=key.warehouse_id,
            ingredient_id=key.ingredient_id,
        ).first()
        if stock_row is None:
            raise ResourceNotFound("Stock projection for movement was not found.")
        # Mapping the projection verifies its references before the ledger append.
        stock_to_domain(stock_row)
        row = movement_to_orm(movement, stock_row)
        try:
            # Keep a uniqueness failure inside a savepoint so the outer
            # Inventory UnitOfWork remains usable long enough to translate it
            # to the stable application conflict contract.
            with transaction.atomic():
                row.save(force_insert=True)
        except IntegrityError as error:
            raise OperationConflict(
                "A movement already exists for this source identity or reversal target."
            ) from error
