from inventory.application.dto.order_consumption import OrderRequirementIngredientDTO
from inventory.application.exceptions import InvalidApplicationInput, ResourceNotFound
from inventory.application.ports.repositories import IngredientRepository


class ResolveOrderRequirementIngredients:
    """Resolve ingredient display/master data for Sales-owned order snapshots."""

    def __init__(self, ingredients: IngredientRepository) -> None:
        self._ingredients = ingredients

    def execute(
        self, *, business_id: int, ingredient_ids: list[int]
    ) -> tuple[OrderRequirementIngredientDTO, ...]:
        if isinstance(business_id, bool) or not isinstance(business_id, int) or business_id <= 0:
            raise InvalidApplicationInput("Business ID must be a positive integer.")
        if not isinstance(ingredient_ids, list) or not ingredient_ids:
            raise InvalidApplicationInput("At least one ingredient ID is required.")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in ingredient_ids
        ):
            raise InvalidApplicationInput("Ingredient IDs must be positive integers.")

        resolved = []
        for ingredient_id in sorted(set(ingredient_ids)):
            ingredient = self._ingredients.get_by_id_for_business(ingredient_id, business_id)
            if ingredient is None:
                raise ResourceNotFound("An order requirement ingredient was not found in this business.")
            resolved.append(OrderRequirementIngredientDTO(
                id=ingredient.id,
                business_id=ingredient.business_id,
                name=ingredient.name,
                canonical_unit=ingredient.canonical_unit.value,
            ))
        return tuple(resolved)
