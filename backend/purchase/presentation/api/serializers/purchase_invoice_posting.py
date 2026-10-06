from rest_framework import serializers

from purchase.presentation.api.serializers.accounts_payable import AccountsPayableSerializer
from purchase.presentation.api.serializers.purchase_invoice import PurchaseInvoiceSerializer


class PostPurchaseInvoiceRequestSerializer(serializers.Serializer):
    due_date = serializers.DateField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        unexpected = set(self.initial_data) - {"due_date"}
        if unexpected:
            raise serializers.ValidationError({
                field: "This field is server controlled or unsupported."
                for field in sorted(unexpected)
            })
        return attrs


class PostPurchaseInvoiceResponseSerializer(serializers.Serializer):
    invoice = PurchaseInvoiceSerializer()
    accounts_payable = AccountsPayableSerializer()
