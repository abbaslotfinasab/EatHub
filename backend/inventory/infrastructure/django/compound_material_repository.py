from django.db import IntegrityError, connection, transaction
from django.db.models import Q, QuerySet

from inventory.application.dto.compound_material import (
    CompoundMaterialComponentDTO,
    CompoundMaterialDTO,
    CompoundMaterialPageDTO,
)
from inventory.application.exceptions import MasterDataConflict
from inventory.domain.exceptions import InventoryDomainError
from inventory.domain.value_objects.quantity import Quantity
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.models import (
    InventoryOperationLine,
    InventoryReservation,
    InventoryReservationLine,
    InventoryV1Stock,
)
from inventory.models import CompoundMaterialComponent, Ingredient, RecipeInput, RecipeOutput


COMPOUND = Ingredient.PreparationLevel.SEMI_PREPARED
RAW = Ingredient.PreparationLevel.RAW
MAX_COMPONENTS = 100


class DjangoCompoundMaterialRepository:
    @staticmethod
    def _rows(business_id: int, *, lock: bool = False) -> QuerySet:
        rows = Ingredient.objects.filter(
            business_id=business_id,
            preparation_level=COMPOUND,
        ).prefetch_related("compound_components__ingredient")
        if lock and connection.in_atomic_block:
            rows = rows.select_for_update(of=("self",))
        return rows

    @staticmethod
    def _dto(row: Ingredient) -> CompoundMaterialDTO:
        components = []
        for line in row.compound_components.all():
            ingredient = line.ingredient
            if (
                ingredient.business_id != row.business_id
                or ingredient.preparation_level != RAW
                or not ingredient.is_active
            ):
                # Fail closed: inconsistent persisted data must not be returned
                # as a valid composition or expose another business's name.
                raise RuntimeError(
                    "Persisted compound composition violates ingredient ownership or eligibility."
                )
            components.append(CompoundMaterialComponentDTO(
                id=line.pk,
                ingredient_id=line.ingredient_id,
                ingredient_name=ingredient.name,
                quantity=line.quantity,
                unit=line.unit,
            ))
        return CompoundMaterialDTO(
            id=row.pk,
            name=row.name,
            sku=row.sku,
            unit=row.unit,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            components=tuple(components),
        )

    @classmethod
    def list_for_business(
        cls,
        business_id: int,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> CompoundMaterialPageDTO:
        rows = cls._rows(business_id)
        if search:
            rows = rows.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        if is_active is not None:
            rows = rows.filter(is_active=is_active)
        count = rows.count()
        offset = (page - 1) * page_size
        return CompoundMaterialPageDTO(
            count=count,
            page=page,
            page_size=page_size,
            results=[
                cls._dto(row)
                for row in rows.order_by("name", "pk")[offset : offset + page_size]
            ],
        )

    @classmethod
    def get_for_business(
        cls, business_id: int, material_id: int, *, lock: bool = False
    ) -> CompoundMaterialDTO | None:
        row = cls._rows(business_id, lock=lock).filter(pk=material_id).first()
        return None if row is None else cls._dto(row)

    @staticmethod
    def _validate_components(business_id: int, components: list[dict]) -> list[tuple[Ingredient, object, str]]:
        if len(components) < 2:
            raise MasterDataConflict("components", "A compound material requires at least two raw ingredients.")
        if len(components) > MAX_COMPONENTS:
            raise MasterDataConflict("components", f"A compound material may contain at most {MAX_COMPONENTS} ingredients.")
        ingredient_ids = [line["ingredient_id"] for line in components]
        if len(set(ingredient_ids)) != len(ingredient_ids):
            raise MasterDataConflict("components", "Each raw ingredient may appear only once.")

        ingredients = Ingredient.objects.filter(
            business_id=business_id,
            preparation_level=RAW,
            is_active=True,
            pk__in=ingredient_ids,
        ).order_by("pk")
        if connection.in_atomic_block:
            ingredients = ingredients.select_for_update(of=("self",))
        by_id = {row.pk: row for row in ingredients}
        if set(by_id) != set(ingredient_ids):
            raise MasterDataConflict(
                "components", "Select active raw ingredients from this business only."
            )

        validated = []
        for line in components:
            ingredient = by_id[line["ingredient_id"]]
            try:
                quantity = Quantity(line["quantity"], Unit(line["unit"]))
                if quantity.amount <= 0:
                    raise MasterDataConflict("components", "Component quantities must be positive.")
                # Validate both dimensional compatibility and lossless V1 precision.
                quantity.convert_to(Unit(ingredient.unit))
            except InventoryDomainError as error:
                raise MasterDataConflict("components", str(error)) from error
            validated.append((ingredient, quantity.amount, quantity.unit.value))
        return validated

    @staticmethod
    def _translate_integrity_error(error: IntegrityError, field: str) -> MasterDataConflict | None:
        cause = error.__cause__
        if cause is not None:
            if getattr(getattr(cause, "diag", None), "constraint_name", None) in {
                "unique_ingredient_name_per_business", "inv_item_business_sku_uq",
            }:
                constraint = getattr(cause.diag, "constraint_name", "")
                return MasterDataConflict(
                    "sku" if constraint == "inv_item_business_sku_uq" else "name",
                    "This value is already used in this business.",
                )
            if connection.vendor == "sqlite" and getattr(cause, "sqlite_errorcode", None) == 2067:
                return MasterDataConflict(field, "This value is already used in this business.")
        return None

    def create(self, business_id: int, values: dict) -> CompoundMaterialDTO:
        unsupported = set(values) - {"name", "sku", "unit", "is_active", "components"}
        if unsupported:
            raise MasterDataConflict("detail", "Unsupported Compound Material fields were provided.")
        header = {
            "name": values["name"].strip(),
            "sku": values.get("sku") or None,
            "unit": values["unit"],
            "is_active": values.get("is_active", True),
        }
        try:
            with transaction.atomic():
                components = self._validate_components(business_id, values["components"])
                row = Ingredient.objects.create(
                    business_id=business_id,
                    preparation_level=COMPOUND,
                    **header,
                )
                CompoundMaterialComponent.objects.bulk_create([
                    CompoundMaterialComponent(
                        compound=row,
                        ingredient=ingredient,
                        quantity=quantity,
                        unit=unit,
                    )
                    for ingredient, quantity, unit in components
                ])
                return self.get_for_business(business_id, row.pk)  # type: ignore[return-value]
        except IntegrityError as error:
            conflict = self._translate_integrity_error(error, "name")
            if conflict is None:
                raise
            raise conflict from error

    def update(self, business_id: int, material_id: int, values: dict) -> CompoundMaterialDTO | None:
        unsupported = set(values) - {"name", "sku", "unit", "is_active", "components"}
        if unsupported:
            raise MasterDataConflict("detail", "Unsupported Compound Material fields were provided.")
        header = {key: values[key] for key in ("name", "sku", "unit", "is_active") if key in values}
        if "name" in header:
            header["name"] = header["name"].strip()
        if "sku" in header:
            header["sku"] = header["sku"] or None

        try:
            with transaction.atomic():
                row = self._rows(business_id, lock=True).filter(pk=material_id).first()
                if row is None:
                    return None
                if "is_active" in header and header["is_active"] is False and InventoryReservationLine.objects.filter(
                    ingredient_id=row.pk,
                    reservation__business_id=business_id,
                    reservation__status=InventoryReservation.Status.ACTIVE,
                ).exists():
                    raise MasterDataConflict(
                        "is_active",
                        "This compound material has an active reservation and cannot be deactivated.",
                    )
                if "unit" in header and header["unit"] != row.unit and (
                    InventoryV1Stock.objects.filter(business_id=business_id, ingredient_id=row.pk).exists()
                    or InventoryOperationLine.objects.filter(operation__business_id=business_id, ingredient_id=row.pk).exists()
                    or RecipeInput.objects.filter(recipe__business_id=business_id, ingredient_id=row.pk).exists()
                    or RecipeOutput.objects.filter(recipe__business_id=business_id, ingredient_id=row.pk).exists()
                    or InventoryReservationLine.objects.filter(
                        ingredient_id=row.pk,
                        reservation__business_id=business_id,
                    ).exists()
                ):
                    raise MasterDataConflict(
                        "unit",
                        "The unit cannot change after this compound material is used by inventory or a recipe.",
                    )
                component_values = (
                    self._validate_components(business_id, values["components"])
                    if "components" in values else None
                )
                for field, value in header.items():
                    setattr(row, field, value)
                if header:
                    row.save(update_fields=(*header.keys(), "updated_at"))
                if component_values is not None:
                    row.compound_components.all().delete()
                    CompoundMaterialComponent.objects.bulk_create([
                        CompoundMaterialComponent(
                            compound=row,
                            ingredient=ingredient,
                            quantity=quantity,
                            unit=unit,
                        )
                        for ingredient, quantity, unit in component_values
                    ])
                return self.get_for_business(business_id, material_id, lock=True)
        except IntegrityError as error:
            conflict = self._translate_integrity_error(error, "name")
            if conflict is None:
                raise
            raise conflict from error
