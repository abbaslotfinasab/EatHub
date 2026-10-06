from rest_framework import serializers


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
