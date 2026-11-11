"""Public composition adapter for business-scoped Recipe queries.

Sales code consumes the Inventory application use case through this composition
boundary and never imports Inventory ORM models or repositories directly.
"""
from inventory.application.use_cases.manage_recipes import (
    ManageRecipes,
    RecipeNotFound,
)
from inventory.infrastructure.django.recipe_repository import DjangoRecipeRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork


class RecipeUnavailable(Exception):
    """A Recipe ID is not available inside the requested business."""


def get_recipe_for_business(*, business_id: int, recipe_id: int):
    """Return an Inventory Recipe DTO only when it belongs to the supplied business."""
    use_case = ManageRecipes(DjangoRecipeRepository(), DjangoInventoryUnitOfWork())
    try:
        return use_case.get(business_id, recipe_id)
    except RecipeNotFound as error:
        raise RecipeUnavailable("Recipe does not exist in this business.") from error
