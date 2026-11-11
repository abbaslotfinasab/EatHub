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

        requested_ids = sorted(set(ingredient_ids))
        rows = self._ingredients.get_many_for_business(requested_ids, business_id)
        by_id = {ingredient.id: ingredient for ingredient in rows}
        if set(by_id) != set(requested_ids):
            raise ResourceNotFound("An order requirement ingredient was not found in this business.")
        return tuple(
            OrderRequirementIngredientDTO(
                id=ingredient.id,
                business_id=ingredient.business_id,
                name=ingredient.name,
                canonical_unit=ingredient.canonical_unit.value,
            )
            for ingredient in (by_id[ingredient_id] for ingredient_id in requested_ids)
        )
