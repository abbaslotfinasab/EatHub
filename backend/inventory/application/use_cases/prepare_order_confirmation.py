from inventory.application.context import InventoryExecutionContext
from inventory.application.dto.order_confirmation import OrderConfirmationInventoryDTO
from inventory.application.exceptions import InvalidApplicationInput, OperationConflict, ResourceNotFound
from inventory.application.ports.recipe_repositories import RecipeRepository, RecipeUnitOfWork
from inventory.application.ports.repositories import WarehouseRepository


class PrepareOrderConfirmation:
    """Resolve and lock Inventory-owned master data before Sales freezes order snapshots."""

    def __init__(self, recipes: RecipeRepository, warehouses: WarehouseRepository,
                 unit_of_work: RecipeUnitOfWork):
        self._recipes = recipes
        self._warehouses = warehouses
        self._unit_of_work = unit_of_work

    def execute(self, context: InventoryExecutionContext, recipe_ids: list[int]) -> OrderConfirmationInventoryDTO:
        if not isinstance(context, InventoryExecutionContext) or context.actor_id is None:
            raise InvalidApplicationInput("A trusted Inventory execution context with actor is required.")
        if not isinstance(recipe_ids, list) or not recipe_ids:
            raise InvalidApplicationInput("At least one recipe is required for order confirmation.")
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in recipe_ids):
            raise InvalidApplicationInput("Recipe IDs must be positive integers.")

        with self._unit_of_work.atomic():
            defaults = self._warehouses.get_active_defaults_for_business(context.business_id, lock=True)
            if len(defaults) != 1:
                raise OperationConflict("Configure exactly one active default warehouse before confirming recipe-based orders.")

            resolved = []
            for recipe_id in sorted(set(recipe_ids)):
                recipe = self._recipes.get_for_business(context.business_id, recipe_id, lock=True)
                if recipe is None:
                    raise ResourceNotFound("A linked recipe was not found in this business.")
                if not recipe.is_active:
                    raise OperationConflict(f"Recipe '{recipe.name}' is inactive.")
                for line in (*recipe.inputs, *recipe.outputs):
                    if line.ingredient_business_id != context.business_id or not line.ingredient_is_active:
                        raise OperationConflict("A recipe ingredient is inactive or outside this business.")
                    if not line.ingredient_unit:
                        raise OperationConflict("A recipe ingredient has no canonical inventory unit.")
                resolved.append(recipe)

            return OrderConfirmationInventoryDTO(
                warehouse_id=defaults[0].id,
                recipes=tuple(resolved),
            )
