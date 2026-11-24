from unittest.mock import patch

from django.test import SimpleTestCase

from purchase import composition


class PaymentAllocationCompositionTests(SimpleTestCase):
    @patch("purchase.composition.DjangoAccountsPayableRepository")
    @patch("purchase.composition.DjangoSupplierPaymentRepository")
    @patch("purchase.composition.DjangoPaymentAllocationRepository")
    @patch("purchase.composition.DjangoTransactionManager")
    @patch("purchase.composition.CreatePaymentAllocation")
    def test_create_use_case_wires_all_repositories_and_transaction_manager(
        self, use_case_class, transaction_manager_class,
        allocation_repository_class, supplier_payment_repository_class,
        accounts_payable_repository_class,
    ):
        result = composition.create_payment_allocation_use_case()
        accounts_payable_repository_class.assert_called_once_with()
        supplier_payment_repository_class.assert_called_once_with()
        allocation_repository_class.assert_called_once_with()
        transaction_manager_class.assert_called_once_with()
        use_case_class.assert_called_once_with(
            accounts_payable_repository_class.return_value,
            supplier_payment_repository_class.return_value,
            allocation_repository_class.return_value,
            transaction_manager_class.return_value,
        )
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.DjangoPaymentAllocationRepository")
    @patch("purchase.composition.ListPaymentAllocations")
    def test_list_use_case_is_wired_to_allocation_repository(
        self, use_case_class, repository_class,
    ):
        result = composition.list_payment_allocations_use_case()
        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.DjangoPaymentAllocationRepository")
    @patch("purchase.composition.GetPaymentAllocation")
    def test_get_use_case_is_wired_to_allocation_repository(
        self, use_case_class, repository_class,
    ):
        result = composition.get_payment_allocation_use_case()
        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)
