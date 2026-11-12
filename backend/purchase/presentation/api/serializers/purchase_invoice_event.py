from rest_framework import serializers

from purchase.models import PurchaseInvoiceEvent


class PurchaseInvoiceEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.name", allow_null=True, read_only=True)

    class Meta:
        model = PurchaseInvoiceEvent
        fields = (
            "id",
            "event_type",
            "actor_id",
            "actor_name",
            "previous_status",
            "resulting_status",
            "metadata",
            "occurred_at",
        )
        read_only_fields = fields
