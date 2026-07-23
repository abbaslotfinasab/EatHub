from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    today_sales = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
    )

    today_orders = serializers.IntegerField()

    active_orders = serializers.IntegerField()

    today_reservations = serializers.IntegerField()

    inventory_alerts = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    stats = DashboardStatsSerializer()

    sales_chart = serializers.ListField()

    recent_orders = serializers.ListField()

    inventory_alerts = serializers.ListField()

    top_products = serializers.ListField()

    activities = serializers.ListField()