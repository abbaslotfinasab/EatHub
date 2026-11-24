from unittest.mock import patch

from django.test import SimpleTestCase

from purchase import composition


class SupplierPaymentCompositionTests(SimpleTestCase):
    @patch("purchase.composition.DjangoSupplierRepository")
    @patch("purchase.composition.DjangoSupplierPaymentRepository")
    @patch("purchase.composition.CreateSupplierPaymentUseCase")
    def test_create_use_case_wires_payment_and_supplier_repositories(
        self,
        use_case_class,
        payment_repository_class,
        supplier_repository_class,
    ):
        result = composition.create_supplier_payment_use_case()

        payment_repository_class.assert_called_once_with()
        supplier_repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(
            payment_repository_class.return_value,
            supplier_repository_class.return_value,
        )
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.DjangoSupplierPaymentRepository")
    @patch("purchase.composition.ListSupplierPaymentsUseCase")
    def test_list_use_case_wires_payment_repository(
        self, use_case_class, repository_class,
    ):
        result = composition.list_supplier_payments_use_case()

        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.DjangoSupplierPaymentRepository")
    @patch("purchase.composition.GetSupplierPaymentUseCase")
    def test_get_use_case_wires_payment_repository(
        self, use_case_class, repository_class,
    ):
        result = composition.get_supplier_payment_use_case()

        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.DjangoPaymentAllocationRepository")
    @patch("purchase.composition.ListSupplierPaymentAllocationTotalsUseCase")
    def test_allocation_totals_use_case_wires_allocation_repository(
        self, use_case_class, repository_class,
    ):
        result = composition.list_supplier_payment_allocation_totals_use_case()

        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)
