from unittest.mock import patch

from django.test import SimpleTestCase

from purchase import composition


class AccountsPayableCompositionTests(SimpleTestCase):
    @patch("purchase.composition.ListAccountsPayablesUseCase")
    @patch("purchase.composition.DjangoAccountsPayableRepository")
    def test_list_use_case_is_wired_to_accounts_payable_repository(
        self,
        repository_class,
        use_case_class,
    ):
        result = composition.list_accounts_payables_use_case()

        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.GetAccountsPayableUseCase")
    @patch("purchase.composition.DjangoAccountsPayableRepository")
    def test_get_use_case_is_wired_to_accounts_payable_repository(
        self,
        repository_class,
        use_case_class,
    ):
        result = composition.get_accounts_payable_use_case()

        repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(repository_class.return_value)
        self.assertIs(result, use_case_class.return_value)

    @patch("purchase.composition.GetAccountsPayablePaymentEligibility")
    @patch("purchase.composition.DjangoPaymentAllocationRepository")
    @patch("purchase.composition.DjangoAccountsPayableRepository")
    def test_payment_eligibility_wires_both_repositories(
        self,
        payable_repository_class,
        allocation_repository_class,
        use_case_class,
    ):
        result = composition.accounts_payable_payment_eligibility_use_case()

        payable_repository_class.assert_called_once_with()
        allocation_repository_class.assert_called_once_with()
        use_case_class.assert_called_once_with(
            payable_repository_class.return_value,
            allocation_repository_class.return_value,
        )
        self.assertIs(result, use_case_class.return_value)
