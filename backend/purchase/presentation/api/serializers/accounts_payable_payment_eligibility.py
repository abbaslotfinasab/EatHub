from rest_framework import serializers

from purchase.domain.enums.accounts_payable_payment_eligibility_reason import (
    AccountsPayablePaymentEligibilityReason,
)
from purchase.domain.enums.accounts_payable_status import AccountsPayableStatus


class AccountsPayablePaymentEligibilitySerializer(serializers.Serializer):
    accounts_payable_id = serializers.IntegerField()
    eligible = serializers.BooleanField()
    status = serializers.ChoiceField(
        choices=[status.value for status in AccountsPayableStatus],
    )
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    reason = serializers.ChoiceField(
        choices=[reason.value for reason in AccountsPayablePaymentEligibilityReason],
        allow_null=True,
    )
