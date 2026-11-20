from unittest import TestCase
from unittest.mock import Mock

from catalog.application.exceptions import ProductsUnavailable
from catalog.application.use_cases.resolve_active_products import ResolveActiveProducts


class ResolveActiveProductsTests(TestCase):
    def setUp(self):
        self.repository = Mock()
        self.use_case = ResolveActiveProducts(self.repository)

    def test_empty_ids_return_empty_mapping_without_repository_query(self):
        self.assertEqual(
            self.use_case.execute(business_id=7, product_ids=set()),
            {},
        )
        self.repository.get_active_products_for_business.assert_not_called()

    def test_returns_products_resolved_for_business(self):
        products = {11: object(), 12: object()}
        self.repository.get_active_products_for_business.return_value = products

        result = self.use_case.execute(business_id=7, product_ids={11, 12})

        self.assertEqual(result, products)
        self.repository.get_active_products_for_business.assert_called_once_with(
            business_id=7,
            product_ids={11, 12},
        )

    def test_rejects_missing_inactive_or_foreign_products(self):
        self.repository.get_active_products_for_business.return_value = {11: object()}

        with self.assertRaises(ProductsUnavailable):
            self.use_case.execute(business_id=7, product_ids={11, 12})
