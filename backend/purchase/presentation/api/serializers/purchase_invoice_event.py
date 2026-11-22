from rest_framework import serializers


class PurchaseInvoiceEventSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_type = serializers.CharField(read_only=True)
    actor_id = serializers.IntegerField(allow_null=True, read_only=True)
    actor_name = serializers.CharField(allow_null=True, read_only=True)
    previous_status = serializers.CharField(allow_null=True, read_only=True)
    resulting_status = serializers.CharField(allow_null=True, read_only=True)
    metadata = serializers.JSONField(read_only=True)
    occurred_at = serializers.DateTimeField(read_only=True)
