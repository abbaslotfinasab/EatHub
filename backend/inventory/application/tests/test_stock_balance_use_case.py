from decimal import Decimal
from unittest import TestCase

from inventory.application.dto.stock_balance import (
    ListStockBalancesQuery,
    StockBalanceDTO,
    StockBalancePageDTO,
)
from inventory.application.use_cases.list_stock_balances import (
    ListStockBalancesUseCase,
)
from inventory.domain.entities.ingredient import Ingredient
from inventory.domain.entities.warehouse import Warehouse
from inventory.domain.value_objects.unit import Unit


class FakeIngredientRepository:
    def __init__(self, ingredient=None):
        self.ingredient = ingredient

    def get_by_id_for_business(self, ingredient_id, business_id):
        if self.ingredient and (
            self.ingredient.id == ingredient_id
            and self.ingredient.business_id == business_id
        ):
            return self.ingredient
        return None


class FakeWarehouseRepository:
    def __init__(self, warehouse=None):
        self.warehouse = warehouse

    def get_by_id_for_business(self, warehouse_id, business_id):
        if self.warehouse and (
            self.warehouse.id == warehouse_id
            and self.warehouse.business_id == business_id
        ):
            return self.warehouse
        return None


class FakeStockBalanceRepository:
    def __init__(self):
        self.query = None

    def list_for_business(self, query):
        self.query = query
        item = StockBalanceDTO(
            id=8,
            ingredient_id=3,
            ingredient_name="Flour",
            warehouse_id=5,
            warehouse_name="Main",
            quantity=Decimal("1.250000000000"),
            unit=Unit.KG,
            average_cost=Decimal("2.500000000000"),
        )
        return StockBalancePageDTO(1, query.page, query.page_size, [item])


class ListStockBalancesUseCaseTests(TestCase):
    def setUp(self):
        self.balances = FakeStockBalanceRepository()
        self.ingredients = FakeIngredientRepository(
            Ingredient(3, 10, "Flour", Unit.KG)
        )
        self.warehouses = FakeWarehouseRepository(
            Warehouse(5, 10, "Main", is_active=True, is_default=True)
        )
        self.use_case = ListStockBalancesUseCase(
            self.balances, self.ingredients, self.warehouses
        )

    def test_validates_business_scoped_filters_and_passes_page(self):
        result = self.use_case.execute(
            ListStockBalancesQuery(
                business_id=10,
                page=2,
                page_size=25,
                ingredient_id=3,
                warehouse_id=5,
            )
        )

        self.assertEqual((result.count, result.page, result.page_size), (1, 2, 25))
        self.assertEqual(self.balances.query.business_id, 10)
        self.assertEqual(self.balances.query.ingredient_id, 3)
        self.assertEqual(self.balances.query.warehouse_id, 5)
        self.assertEqual(result.results[0].quantity, Decimal("1.250000000000"))

    def test_rejects_foreign_or_missing_filter_references(self):
        with self.assertRaisesRegex(ValueError, "Ingredient was not found"):
            self.use_case.execute(
                ListStockBalancesQuery(business_id=10, ingredient_id=99)
            )
        self.assertIsNone(self.balances.query)

        with self.assertRaisesRegex(ValueError, "Warehouse was not found"):
            self.use_case.execute(
                ListStockBalancesQuery(business_id=10, warehouse_id=99)
            )
        self.assertIsNone(self.balances.query)

    def test_rejects_invalid_page_values_and_oversized_page(self):
        for query in (
            ListStockBalancesQuery(business_id=10, page=0),
            ListStockBalancesQuery(business_id=10, page_size=0),
            ListStockBalancesQuery(business_id=10, page_size=101),
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                self.use_case.execute(query)
