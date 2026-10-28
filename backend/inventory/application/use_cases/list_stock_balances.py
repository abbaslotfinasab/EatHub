from inventory.application.dto.stock_balance import (
    ListStockBalancesQuery,
    StockBalancePageDTO,
)
from inventory.application.ports.repositories import (
    IngredientRepository,
    StockBalanceRepository,
    WarehouseRepository,
)


class ListStockBalancesUseCase:
    MAX_PAGE_SIZE = 100

    def __init__(
        self,
        balances: StockBalanceRepository,
        ingredients: IngredientRepository,
        warehouses: WarehouseRepository,
    ) -> None:
        self._balances = balances
        self._ingredients = ingredients
        self._warehouses = warehouses

    def execute(self, query: ListStockBalancesQuery) -> StockBalancePageDTO:
        if not isinstance(query.business_id, int) or query.business_id <= 0:
            raise ValueError("Business ID must be a positive integer.")
        if not isinstance(query.page, int) or query.page <= 0:
            raise ValueError("Page must be a positive integer.")
        if (
            not isinstance(query.page_size, int)
            or query.page_size <= 0
            or query.page_size > self.MAX_PAGE_SIZE
        ):
            raise ValueError("Page size must be between 1 and 100.")

        if query.material_type not in (None, "raw", "compound"):
            raise ValueError("Material type must be raw or compound.")

        if query.ingredient_id is not None:
            if (
                not isinstance(query.ingredient_id, int)
                or query.ingredient_id <= 0
            ):
                raise ValueError("Ingredient ID must be a positive integer.")
            if self._ingredients.get_by_id_for_business(
                query.ingredient_id, query.business_id
            ) is None:
                raise ValueError("Ingredient was not found in this Business.")

        if query.warehouse_id is not None:
            if (
                not isinstance(query.warehouse_id, int)
                or query.warehouse_id <= 0
            ):
                raise ValueError("Warehouse ID must be a positive integer.")
            if self._warehouses.get_by_id_for_business(
                query.warehouse_id, query.business_id
            ) is None:
                raise ValueError("Warehouse was not found in this Business.")

        return self._balances.list_for_business(query)
