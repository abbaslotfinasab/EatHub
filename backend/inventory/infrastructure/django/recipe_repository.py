from django.db import connection
from django.db.models import Q, QuerySet

from inventory.application.dto.recipe import RecipeDTO, RecipeLineDTO, RecipePageDTO
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.recipe import Recipe
from inventory.domain.entities.recipe_input import RecipeInput
from inventory.domain.entities.recipe_output import RecipeOutput
from inventory.domain.exceptions import TenantMismatch
from inventory.infrastructure.django.mappers import ingredient_to_domain
from inventory.models import Ingredient as IngredientModel
from inventory.models import Recipe as RecipeModel
from inventory.models import RecipeInput as RecipeInputModel
from inventory.models import RecipeOutput as RecipeOutputModel


class DjangoRecipeRepository:
    @staticmethod
    def _recipes(business_id: int, *, lock: bool = False) -> QuerySet:
        rows = RecipeModel.objects.filter(business_id=business_id).prefetch_related(
            "inputs__ingredient", "outputs__ingredient",
        )
        if lock and connection.in_atomic_block:
            rows = rows.select_for_update(of=("self",))
        return rows

    @staticmethod
    def _dto(row: RecipeModel) -> RecipeDTO:
        inputs = tuple(
            RecipeLineDTO(
                id=line.pk,
                ingredient_id=line.ingredient_id,
                ingredient_name=line.ingredient.name,
                quantity=line.quantity,
                unit=line.unit,
                notes=line.notes,
                material_type="compound" if line.ingredient.preparation_level == "semi_prepared" else "raw",
            )
            for line in row.inputs.all()
        )
        outputs = tuple(
            RecipeLineDTO(
                id=line.pk,
                ingredient_id=line.ingredient_id,
                ingredient_name=line.ingredient.name,
                quantity=line.quantity,
                unit=line.unit,
                notes=line.notes,
                is_primary=line.is_primary,
                material_type="compound" if line.ingredient.preparation_level == "semi_prepared" else "raw",
            )
            for line in row.outputs.all()
        )
        if any(line.ingredient.business_id != row.business_id for line in (*row.inputs.all(), *row.outputs.all())):
            raise TenantMismatch("Persisted Recipe references an Ingredient from another Business.")
        return RecipeDTO(
            id=row.pk,
            business_id=row.business_id,
            name=row.name,
            code=row.code,
            type=row.type,
            description=row.description,
            is_active=row.is_active,
            inputs=inputs,
            outputs=outputs,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def list_for_business(
        self, business_id: int, *, page: int, page_size: int,
        search: str | None, recipe_type: str | None, is_active: bool | None,
    ) -> RecipePageDTO:
        rows = RecipeModel.objects.filter(business_id=business_id)
        if search:
            rows = rows.filter(Q(name__icontains=search) | Q(code__icontains=search))
        if recipe_type is not None:
            rows = rows.filter(type=recipe_type)
        if is_active is not None:
            rows = rows.filter(is_active=is_active)
        count = rows.count()
        offset = (page - 1) * page_size
        results = rows.order_by("name", "pk")[offset:offset + page_size].prefetch_related(
            "inputs__ingredient", "outputs__ingredient",
        )
        return RecipePageDTO(
            count=count,
            page=page,
            page_size=page_size,
            results=tuple(self._dto(row) for row in results),
        )

    def get_for_business(
        self, business_id: int, recipe_id: int, *, lock: bool = False,
    ) -> RecipeDTO | None:
        row = self._recipes(business_id, lock=lock).filter(pk=recipe_id).first()
        return None if row is None else self._dto(row)

    def get_ingredient_for_update(
        self, business_id: int, ingredient_id: int,
    ) -> Ingredient | None:
        rows = IngredientModel.objects.filter(
            business_id=business_id, pk=ingredient_id,
        )
        if connection.in_atomic_block:
            rows = rows.select_for_update()
        row = rows.first()
        return None if row is None else ingredient_to_domain(row)

    def create(
        self, recipe: Recipe, *, code: str | None, description: str | None,
        is_active: bool, inputs: list[RecipeInput], outputs: list[RecipeOutput],
    ) -> RecipeDTO:
        row = RecipeModel.objects.create(
            business_id=recipe.business_id,
            name=recipe.name,
            code=code,
            type=recipe.recipe_type.value,
            description=description,
            is_active=is_active,
        )
        RecipeInputModel.objects.bulk_create([
            RecipeInputModel(
                recipe=row,
                ingredient_id=line.ingredient_id,
                quantity=line.quantity.amount,
                unit=line.quantity.unit.value,
                notes=line.notes,
            )
            for line in inputs
        ])
        RecipeOutputModel.objects.bulk_create([
            RecipeOutputModel(
                recipe=row,
                ingredient_id=line.ingredient_id,
                quantity=line.quantity.amount,
                unit=line.quantity.unit.value,
                is_primary=line.is_primary,
                notes=line.notes,
            )
            for line in outputs
        ])
        return self.get_for_business(recipe.business_id, row.pk)  # type: ignore[return-value]

    def update_header(
        self, business_id: int, recipe_id: int, recipe: Recipe, *,
        code: str | None, description: str | None, is_active: bool,
    ) -> RecipeDTO | None:
        row = RecipeModel.objects.filter(business_id=business_id, pk=recipe_id).first()
        if row is None:
            return None
        row.name = recipe.name
        row.type = recipe.recipe_type.value
        row.code = code
        row.description = description
        row.is_active = is_active
        row.save(update_fields=("name", "type", "code", "description", "is_active", "updated_at"))
        return self.get_for_business(business_id, row.pk)

    def save_line(
        self, business_id: int, recipe_id: int, kind: str,
        line: RecipeInput | RecipeOutput, line_id: int | None = None,
    ) -> RecipeDTO | None:
        recipe = RecipeModel.objects.filter(business_id=business_id, pk=recipe_id).first()
        if recipe is None:
            return None
        if not IngredientModel.objects.filter(
            business_id=business_id, pk=line.ingredient_id,
        ).exists():
            return None
        model = RecipeInputModel if kind == "input" else RecipeOutputModel
        values = {
            "ingredient_id": line.ingredient_id,
            "quantity": line.quantity.amount,
            "unit": line.quantity.unit.value,
            "notes": line.notes,
        }
        if isinstance(line, RecipeOutput):
            values["is_primary"] = line.is_primary
        if line_id is None:
            model.objects.create(recipe=recipe, **values)
        else:
            row = model.objects.filter(recipe=recipe, pk=line_id).first()
            if row is None:
                return None
            for key, value in values.items():
                setattr(row, key, value)
            row.save(update_fields=(*values, "updated_at"))
        return self.get_for_business(business_id, recipe.pk)

    def replace_lines(self, business_id: int, recipe_id: int, kind: str, lines) -> bool:
        recipe = RecipeModel.objects.filter(business_id=business_id, pk=recipe_id).first()
        if recipe is None:
            return False
        model = RecipeInputModel if kind == "input" else RecipeOutputModel
        model.objects.filter(recipe=recipe).delete()
        if kind == "input":
            model.objects.bulk_create([
                RecipeInputModel(
                    recipe=recipe, ingredient_id=line.ingredient_id,
                    quantity=line.quantity.amount, unit=line.quantity.unit.value,
                    notes=line.notes,
                ) for line in lines
            ])
        else:
            model.objects.bulk_create([
                RecipeOutputModel(
                    recipe=recipe, ingredient_id=line.ingredient_id,
                    quantity=line.quantity.amount, unit=line.quantity.unit.value,
                    is_primary=line.is_primary, notes=line.notes,
                ) for line in lines
            ])
        return True

    def delete_line(self, business_id: int, recipe_id: int, kind: str, line_id: int) -> bool:
        model = RecipeInputModel if kind == "input" else RecipeOutputModel
        deleted, _ = model.objects.filter(
            recipe_id=recipe_id,
            recipe__business_id=business_id,
            pk=line_id,
        ).delete()
        return bool(deleted)
