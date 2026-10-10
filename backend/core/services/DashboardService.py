from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Case,
    CharField,
    Count,
    F,
    Min,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Concat
from django.db.models.functions import TruncDate
from django.utils import timezone

from core.models import ActivityLog
from products.models import Order, OrderItem


class DashboardService:

    @classmethod
    def get_dashboard(cls, business, sales_period="weekly"):
        return {
            "stats": cls.get_stats(business),
            "sales_chart": cls.get_sales_chart(business, period=sales_period),
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
    def get_sales_chart(cls, business, period="weekly"):
        today = timezone.localdate()

        if period == "monthly":
            month_start = today.replace(day=1)
            daily_sales = (
                Order.objects.filter(
                    business=business,
                    created_at__date__gte=month_start,
                    created_at__date__lte=today,
                    status=Order.Status.COMPLETED,
                    payment_status=Order.PaymentStatus.PAID,
                )
                .annotate(
                    sale_date=TruncDate(
                        "created_at",
                        tzinfo=timezone.get_current_timezone(),
                    ),
                )
                .values("sale_date")
                .annotate(
                    total=Coalesce(
                        Sum("total_amount"),
                        Decimal("0.00"),
                        output_field=Order._meta.get_field("total_amount"),
                    ),
                )
                .order_by("sale_date")
            )
            sales_by_date = {
                row["sale_date"]: row["total"]
                for row in daily_sales
            }
            return [
                {
                    "date": (month_start + timedelta(days=day_offset)).strftime(
                        "%Y-%m-%d"
                    ),
                    "sales": sales_by_date.get(
                        month_start + timedelta(days=day_offset),
                        Decimal("0.00"),
                    ),
                }
                for day_offset in range(today.day)
            ]

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
            .order_by("-created_at", "-id")
        )

        return orders

    @classmethod
    def get_inventory_alerts(cls, business):
        # بعداً از Ingredient پر می‌شود
        return []

    @classmethod
    def get_top_products(cls, business):
        products = list(
            OrderItem.objects
            .filter(
                order__business=business,
                order__status=Order.Status.COMPLETED,
                order__payment_status=Order.PaymentStatus.PAID,
            )
            .annotate(
                product_key=Case(
                    When(
                        menu_item__isnull=True,
                        then=Concat(Value("snapshot:"), F("menu_item_name")),
                    ),
                    default=Concat(
                        Value("menu:"),
                        Cast(F("menu_item_id"), output_field=CharField()),
                    ),
                    output_field=CharField(),
                ),
            )
            .values(
                "product_key",
            )
            .annotate(
                menu_item=Min("menu_item"),
                menu_item_name=Min("menu_item_name"),
                total_sold=Sum("quantity"),
                revenue=Sum("total_price"),
                orders_count=Count("order", distinct=True),
            )
            .order_by("-total_sold")[:5]
        )

        menu_item_ids = [
            product["menu_item"]
            for product in products
            if product["menu_item"] is not None
        ]
        latest_names = {}
        if menu_item_ids:
            latest_snapshots = (
                OrderItem.objects
                .filter(
                    menu_item_id__in=menu_item_ids,
                    order__business=business,
                    order__status=Order.Status.COMPLETED,
                    order__payment_status=Order.PaymentStatus.PAID,
                )
                .order_by("-created_at", "-id")
                .values_list("menu_item_id", "menu_item_name")
            )
            for menu_item_id, name in latest_snapshots:
                latest_names.setdefault(menu_item_id, name)

        for product in products:
            if product["menu_item"] is not None:
                product["menu_item_name"] = latest_names.get(
                    product["menu_item"],
                    product["menu_item_name"],
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
                    activity.user.name
                    if activity.user
                    else None
                ),

                "created_at": activity.created_at,
            }

            for activity in activities
        ]
