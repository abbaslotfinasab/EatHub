from rest_framework import serializers


class CreateAccountsPayableSerializer(serializers.Serializer):
    source_invoice_id = serializers.IntegerField(min_value=1)
    due_date = serializers.DateField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        allowed = {"source_invoice_id", "due_date"}
        supplied = set(self.initial_data)
        unexpected = supplied - allowed
        if unexpected:
            raise serializers.ValidationError({
                field: "This field is server controlled or unsupported."
                for field in sorted(unexpected)
            })
        return attrs


class AccountsPayableSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    source_invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    due_date = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    posted_at = serializers.DateTimeField(allow_null=True)
    posted_by_id = serializers.IntegerField(allow_null=True)
    cancelled_at = serializers.DateTimeField(allow_null=True)
    cancelled_by_id = serializers.IntegerField(allow_null=True)
    cancellation_reason = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
