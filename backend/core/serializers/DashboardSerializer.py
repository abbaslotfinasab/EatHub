from rest_framework import serializers

from products.serializers.order_serializer import OrderSerializer


class DashboardStatsSerializer(serializers.Serializer):
    today_sales = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
    )

    today_orders = serializers.IntegerField()

    active_orders = serializers.IntegerField()

    today_reservations = serializers.IntegerField()

    inventory_alerts = serializers.IntegerField()


class DashboardTopProductSerializer(serializers.Serializer):
    menu_item = serializers.IntegerField()

    menu_item_name = serializers.CharField()

    total_sold = serializers.IntegerField()

    revenue = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    orders_count = serializers.IntegerField()


class DashboardActivitySerializer(serializers.Serializer):
    id = serializers.IntegerField()

    title = serializers.CharField()

    description = serializers.CharField(
        allow_null=True
    )

    action = serializers.CharField()

    user = serializers.CharField(
        allow_null=True
    )

    created_at = serializers.DateTimeField()


class DashboardSerializer(serializers.Serializer):
    stats = DashboardStatsSerializer()

    sales_chart = serializers.ListField()

    recent_orders = OrderSerializer(many=True)

    inventory_alerts = serializers.ListField()

    top_products = DashboardTopProductSerializer(
        many=True
    )

    activities = DashboardActivitySerializer(
        many=True
    )
