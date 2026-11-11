from dataclasses import dataclass

from inventory.application.dto.recipe import RecipeDTO


@dataclass(frozen=True, slots=True)
class OrderConfirmationInventoryDTO:
    warehouse_id: int
    recipes: tuple[RecipeDTO, ...]
