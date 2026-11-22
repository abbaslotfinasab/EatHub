from decimal import Decimal
from unittest.mock import Mock

from django.test import SimpleTestCase

from purchase.application.dto.supplier_payment_allocation import (
    ListSupplierPaymentAllocationTotalsQuery,
)
from purchase.application.use_cases.supplier_payment.list_supplier_payment_allocation_totals import (
    ListSupplierPaymentAllocationTotalsUseCase,
)


class ListSupplierPaymentAllocationTotalsUseCaseTests(SimpleTestCase):
    def setUp(self):
        self.repository = Mock()
        self.use_case = ListSupplierPaymentAllocationTotalsUseCase(self.repository)

    def test_delegates_grouped_read_with_unique_payment_ids(self):
        expected = {10: Decimal("12.50"), 11: Decimal("7.25")}
        self.repository.allocated_amounts_for_supplier_payments.return_value = expected

        result = self.use_case.execute(
            ListSupplierPaymentAllocationTotalsQuery(
                business_id=3,
                supplier_payment_ids=[10, 11, 10],
            )
        )

        self.assertEqual(result, expected)
        self.repository.allocated_amounts_for_supplier_payments.assert_called_once_with(
            3, [10, 11]
        )

    def test_empty_payment_ids_do_not_call_repository(self):
        result = self.use_case.execute(
            ListSupplierPaymentAllocationTotalsQuery(
                business_id=3,
                supplier_payment_ids=[],
            )
        )

        self.assertEqual(result, {})
        self.repository.allocated_amounts_for_supplier_payments.assert_not_called()

    def test_rejects_invalid_business_id(self):
        with self.assertRaisesRegex(ValueError, "Business ID"):
            self.use_case.execute(
                ListSupplierPaymentAllocationTotalsQuery(
                    business_id=0,
                    supplier_payment_ids=[10],
                )
            )

    def test_rejects_invalid_payment_ids(self):
        with self.assertRaisesRegex(ValueError, "Supplier payment IDs"):
            self.use_case.execute(
                ListSupplierPaymentAllocationTotalsQuery(
                    business_id=3,
                    supplier_payment_ids=[10, 0],
                )
            )
