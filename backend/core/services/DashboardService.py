from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import ActivityLog
from products.models import Order, OrderItem


class DashboardService:

    @classmethod
    def get_dashboard(cls, business):
        return {
            "stats": cls.get_stats(business),
            "sales_chart": cls.get_sales_chart(business),
            "recent_orders": cls.get_recent_orders(business),
            "inventory_alerts": cls.get_inventory_alerts(business),
            "top_products": cls.get_top_products(business),
            "activities": cls.get_activities(business),
        }

    @classmethod
    def get_stats(cls, business):
        today = timezone.localdate()

        today_orders = Order.objects.filter(
            business=business,
            created_at__date=today,
            status=Order.Status.COMPLETED,
        )

        today_orders_count = today_orders.count()

        today_sales = (
            today_orders.filter(
                payment_status= Order.PaymentStatus.PAID
            ).aggregate(
                total=Coalesce(
                    Sum("total_amount"),
                    Decimal("0.00"),
                    output_field=Order._meta.get_field("total_amount"),
                )
            )["total"]
        )

        active_orders = Order.objects.filter(
            business=business,
            status__in=[
                Order.Status.PENDING,
                Order.Status.PREPARING,
                Order.Status.READY,
            ],
        ).count()

        return {
            "today_sales": today_sales,
            "today_orders": today_orders_count,
            "active_orders": active_orders,
            "today_reservations": 0,
            "inventory_alerts": 0,
        }

    @classmethod
    def get_sales_chart(cls, business):
        today = timezone.localdate()

        data = []

        for i in range(6, -1, -1):
            date = today - timedelta(days=i)

            total = (
                Order.objects.filter(
                    business=business,
                    created_at__date=date,
                    status=Order.Status.COMPLETED,
                    payment_status=Order.PaymentStatus.PAID,
                ).aggregate(
                    total=Coalesce(
                        Sum("total_amount"),
                        Decimal("0.00"),
                        output_field=Order._meta.get_field("total_amount"),
                    )
                )["total"]
            )

            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "sales": total,
            })

        return data

    @classmethod
    def get_recent_orders(cls, business):
        today = timezone.localdate()

        orders = (
            Order.objects.filter(
                business=business,
                created_at__date=today,

            )
            .select_related("customer")
            .order_by("-created_at")
        )

        return orders

    @classmethod
    def get_inventory_alerts(cls, business):
        # بعداً از Ingredient پر می‌شود
        return []

    @classmethod
    def get_top_products(cls, business):
        products = (
            OrderItem.objects
            .filter(
                order__business=business,
                order__status=Order.Status.COMPLETED,
                order__payment_status=Order.PaymentStatus.PAID,
            )
            .values(
                "menu_item",
                "menu_item_name",
            )
            .annotate(
                total_sold=Sum("quantity"),
                revenue=Sum("total_price"),
                orders_count=Count("order", distinct=True),
            )
            .order_by("-total_sold")[:5]
        )

        return products

    @classmethod
    def get_activities(cls, business):
        activities = (
            ActivityLog.objects
            .filter(
                business=business,
            )
            .select_related("user")
            .order_by("-created_at")[:10]
        )

        return [
            {
                "id": activity.id,

                "title": activity.title,

                "description": activity.description,

                "action": activity.action,

                "user": (
                    activity.user.get_full_name()
                    if activity.user
                    else None
                ),

                "created_at": activity.created_at,
            }

            for activity in activities
        ]