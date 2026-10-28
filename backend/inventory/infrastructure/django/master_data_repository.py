from django.db import IntegrityError, connection, transaction
from django.db.models import Q

from accounts.models import Business
from inventory.application.dto.master_data import InventoryItemDTO, WarehouseDTO
from inventory.application.exceptions import MasterDataConflict
from inventory.infrastructure.django.models import (
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
)
from inventory.models import CompoundMaterialComponent, Ingredient, Warehouse
from inventory.models import RecipeInput, RecipeOutput


_CONSTRAINT_FIELDS = {
    "unique_ingredient_name_per_business": "name",
    "inv_item_business_sku_uq": "sku",
    "unique_warehouse_name_per_business": "name",
    "inv_wh_active_default_uq": "is_default",
}
_ITEM_WRITABLE_FIELDS = {"name", "sku", "unit", "preparation_level", "is_active"}
_WAREHOUSE_WRITABLE_FIELDS = {"name", "code", "is_active", "is_default"}


def _conflict_field(error: IntegrityError) -> str | None:
    cause = error.__cause__
    if cause is None or (
        getattr(cause, "pgcode", None) or getattr(cause, "sqlstate", None)
    ) != "23505":
        return None
    constraint = getattr(getattr(cause, "diag", None), "constraint_name", None)
    return _CONSTRAINT_FIELDS.get(constraint)


def _is_sqlite_unique_violation(error: IntegrityError) -> bool:
    cause = error.__cause__
    return getattr(cause, "sqlite_errorcode", None) == 2067


class DjangoMasterDataRepository:
    """Tenant-scoped persistence for Item and Warehouse master records."""

    @staticmethod
    def _item_dto(row: Ingredient) -> InventoryItemDTO:
        return InventoryItemDTO(
            id=row.pk, name=row.name, sku=row.sku, unit=row.unit,
            preparation_level=row.preparation_level, is_active=row.is_active,
            created_at=row.created_at, updated_at=row.updated_at,
        )

    @staticmethod
    def _warehouse_dto(row: Warehouse) -> WarehouseDTO:
        return WarehouseDTO(
            id=row.pk, name=row.name, code=row.code, is_active=row.is_active,
            is_default=row.is_default, created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def list_items(
        business_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_active: bool | None = None,
        unit: str | None = None,
        preparation_level: str | None = None,
    ) -> tuple[int, list[InventoryItemDTO]]:
        rows = Ingredient.objects.filter(business_id=business_id)
        if search:
            rows = rows.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        if is_active is not None:
            rows = rows.filter(is_active=is_active)
        if unit:
            rows = rows.filter(unit=unit)
        if preparation_level:
            rows = rows.filter(preparation_level=preparation_level)
        count = rows.count()
        offset = (page - 1) * page_size
        return count, [
            DjangoMasterDataRepository._item_dto(row)
            for row in rows.order_by("name", "pk")[offset : offset + page_size]
        ]

    @staticmethod
    def get_item(business_id: int, item_id: int) -> InventoryItemDTO | None:
        row = Ingredient.objects.filter(
            business_id=business_id, pk=item_id
        ).first()
        return None if row is None else DjangoMasterDataRepository._item_dto(row)

    def save_item(
        self, business_id: int, item_id: int | None, values: dict
    ) -> InventoryItemDTO | None:
        unsupported = set(values) - _ITEM_WRITABLE_FIELDS
        if unsupported:
            raise ValueError(f"Unsupported Item fields: {sorted(unsupported)}")
        if values.get("preparation_level") == Ingredient.PreparationLevel.SEMI_PREPARED:
            raise MasterDataConflict(
                "preparation_level",
                "Compound materials must be created and managed through the Compound Materials API.",
            )
        item = (
            Ingredient.objects.filter(business_id=business_id, pk=item_id).first()
            if item_id is not None else None
        )
        if item_id is not None and item is None:
            return None
        if item is not None and item.preparation_level == Ingredient.PreparationLevel.SEMI_PREPARED:
            raise MasterDataConflict(
                "preparation_level",
                "Compound materials must be edited through the Compound Materials API.",
            )

        if "sku" in values and values["sku"]:
            duplicate_sku = Ingredient.objects.filter(
                business_id=business_id, sku=values["sku"]
            )
            if item is not None:
                duplicate_sku = duplicate_sku.exclude(pk=item.pk)
            if duplicate_sku.exists():
                raise MasterDataConflict("sku", "This SKU is already used in this business.")

        if "name" in values:
            duplicate_name = Ingredient.objects.filter(
                business_id=business_id, name=values["name"]
            )
            if item is not None:
                duplicate_name = duplicate_name.exclude(pk=item.pk)
            if duplicate_name.exists():
                raise MasterDataConflict("name", "This name is already used in this business.")

        try:
            with transaction.atomic():
                if item is None:
                    item = Ingredient(business_id=business_id, **values)
                else:
                    item = Ingredient.objects.select_for_update().get(
                        business_id=business_id, pk=item.pk,
                    )
                    if item.preparation_level == Ingredient.PreparationLevel.SEMI_PREPARED:
                        raise MasterDataConflict(
                            "preparation_level",
                            "Compound materials must be edited through the Compound Materials API.",
                        )
                    if values.get("is_active") is False and CompoundMaterialComponent.objects.filter(
                        ingredient_id=item.pk,
                        compound__business_id=business_id,
                        compound__preparation_level=Ingredient.PreparationLevel.SEMI_PREPARED,
                    ).exists():
                        raise MasterDataConflict(
                            "is_active",
                            "This ingredient is used in a compound material. Remove it from each composition before deactivating it.",
                        )
                    if values.get("is_active") is False and InventoryReservationLine.objects.filter(
                        ingredient_id=item.pk,
                        reservation__business_id=business_id,
                        reservation__status=InventoryReservation.Status.ACTIVE,
                    ).exists():
                        raise MasterDataConflict(
                            "is_active",
                            "This ingredient has an active reservation and cannot be deactivated.",
                        )
                    if values.get("unit") and values["unit"] != item.unit:
                        has_references = (
                            InventoryV1Stock.objects.filter(business_id=business_id, ingredient_id=item.pk).exists()
                            or InventoryOperationLine.objects.filter(operation__business_id=business_id, ingredient_id=item.pk).exists()
                            or RecipeInput.objects.filter(recipe__business_id=business_id, ingredient_id=item.pk).exists()
                            or RecipeOutput.objects.filter(recipe__business_id=business_id, ingredient_id=item.pk).exists()
                            or InventoryReservationLine.objects.filter(
                                ingredient_id=item.pk,
                                reservation__business_id=business_id,
                            ).exists()
                            or CompoundMaterialComponent.objects.filter(
                                ingredient_id=item.pk, compound__business_id=business_id,
                            ).exists()
                        )
                        if has_references:
                            raise MasterDataConflict(
                                "unit",
                                "The unit cannot change after this material is referenced by inventory, an operation, a recipe, or a compound composition.",
                            )
                    for field, value in values.items():
                        setattr(item, field, value)
                item.save()
        except IntegrityError as error:
            field = _conflict_field(error)
            if field is None and connection.vendor == "sqlite" and _is_sqlite_unique_violation(error):
                if values.get("sku"):
                    duplicate = Ingredient.objects.filter(
                        business_id=business_id, sku=values["sku"]
                    )
                    if item is not None:
                        duplicate = duplicate.exclude(pk=item.pk)
                    if duplicate.exists():
                        field = "sku"
                if field is None and values.get("name"):
                    duplicate = Ingredient.objects.filter(
                        business_id=business_id, name=values["name"]
                    )
                    if item is not None:
                        duplicate = duplicate.exclude(pk=item.pk)
                    if duplicate.exists():
                        field = "name"
            if field is None:
                raise
            raise MasterDataConflict(
                field, f"This {field.replace('_', ' ')} conflicts with another record."
            ) from error
        return self._item_dto(item)

    @staticmethod
    def list_warehouses(
        business_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_active: bool | None = None,
        is_default: bool | None = None,
    ) -> tuple[int, list[WarehouseDTO]]:
        rows = Warehouse.objects.filter(business_id=business_id)
        if search:
            rows = rows.filter(Q(name__icontains=search) | Q(code__icontains=search))
        if is_active is not None:
            rows = rows.filter(is_active=is_active)
        if is_default is not None:
            rows = rows.filter(is_default=is_default)
        count = rows.count()
        offset = (page - 1) * page_size
        return count, [
            DjangoMasterDataRepository._warehouse_dto(row)
            for row in rows.order_by("name", "pk")[offset : offset + page_size]
        ]

    @staticmethod
    def get_warehouse(business_id: int, warehouse_id: int) -> WarehouseDTO | None:
        row = Warehouse.objects.filter(
            business_id=business_id, pk=warehouse_id
        ).first()
        return None if row is None else DjangoMasterDataRepository._warehouse_dto(row)

    def save_warehouse(
        self, business_id: int, warehouse_id: int | None, values: dict
    ) -> WarehouseDTO | None:
        unsupported = set(values) - _WAREHOUSE_WRITABLE_FIELDS
        if unsupported:
            raise ValueError(f"Unsupported Warehouse fields: {sorted(unsupported)}")
        try:
            with transaction.atomic():
                # Serializes default changes for this business, including the
                # first-default case where no Warehouse row exists to lock.
                Business.objects.select_for_update().get(pk=business_id)
                warehouse = (
                    Warehouse.objects.select_for_update().filter(
                        business_id=business_id, pk=warehouse_id
                    ).first()
                    if warehouse_id is not None
                    else None
                )
                if warehouse_id is not None and warehouse is None:
                    return None
                if (
                    warehouse is not None
                    and values.get("is_active") is False
                    and InventoryReservation.objects.filter(
                        business_id=business_id,
                        warehouse_id=warehouse.pk,
                        status=InventoryReservation.Status.ACTIVE,
                    ).exists()
                ):
                    raise MasterDataConflict(
                        "is_active",
                        "This warehouse has active reservations and cannot be deactivated.",
                    )

                if "name" in values:
                    duplicate_name = Warehouse.objects.filter(
                        business_id=business_id, name=values["name"]
                    )
                    if warehouse is not None:
                        duplicate_name = duplicate_name.exclude(pk=warehouse.pk)
                    if duplicate_name.exists():
                        raise MasterDataConflict(
                            "name", "This name is already used in this business."
                        )

                effective_active = values.get(
                    "is_active", warehouse.is_active if warehouse else True
                )
                requested_default = values.get(
                    "is_default", warehouse.is_default if warehouse else False
                )
                if values.get("is_default") is True and not effective_active:
                    raise MasterDataConflict(
                        "is_default", "An inactive warehouse cannot be the default."
                    )
                effective_default = requested_default and effective_active

                if effective_default:
                    defaults = Warehouse.objects.filter(
                        business_id=business_id,
                        is_active=True,
                        is_default=True,
                    )
                    if warehouse is not None:
                        defaults = defaults.exclude(pk=warehouse.pk)
                    defaults.update(is_default=False)

                if warehouse is None:
                    warehouse = Warehouse(business_id=business_id, **values)
                else:
                    for field, value in values.items():
                        setattr(warehouse, field, value)
                    # Deactivating the current default clears it in the same
                    # transaction and leaves no inactive default marker.
                    if not effective_active and warehouse.is_default:
                        warehouse.is_default = False
                warehouse.save()
        except IntegrityError as error:
            field = _conflict_field(error)
            if field is None and connection.vendor == "sqlite" and _is_sqlite_unique_violation(error):
                if values.get("name"):
                    duplicate = Warehouse.objects.filter(
                        business_id=business_id, name=values["name"]
                    )
                    if warehouse is not None:
                        duplicate = duplicate.exclude(pk=warehouse.pk)
                    if duplicate.exists():
                        field = "name"
                should_be_default = (
                    values.get("is_default", warehouse.is_default if warehouse else False)
                    and values.get("is_active", warehouse.is_active if warehouse else True)
                )
                if field is None and should_be_default:
                    defaults = Warehouse.objects.filter(
                        business_id=business_id, is_active=True, is_default=True
                    )
                    if warehouse is not None:
                        defaults = defaults.exclude(pk=warehouse.pk)
                    if defaults.exists():
                        field = "is_default"
            if field is None:
                raise
            raise MasterDataConflict(
                field, f"This {field.replace('_', ' ')} conflicts with another record."
            ) from error
        return self._warehouse_dto(warehouse)
