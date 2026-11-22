"""Django-backed tenant-scoped read queries for orders."""

from decimal import Decimal

from django.db.models import Q

from products.models import Order


class DjangoOrderReadRepository:
    """Encapsulate order list filtering, ordering, and tenant-scoped lookup."""

    def list_for_business(self, business_id, params):
        filters = Q(business_id=business_id)

        search = params.get("search", "").strip()
        if search:
            filters &= (
                Q(id__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(customer__phone__icontains=search)
            )

        status = params.get("status")
        if status:
            filters &= Q(status=status)

        order_type = params.get("order_type")
        if order_type:
            filters &= Q(order_type=order_type)

        payment_status = params.get("payment_status")
        if payment_status:
            filters &= Q(payment_status=payment_status)

        payment_method = params.get("payment_method")
        if payment_method:
            filters &= Q(payment_method=payment_method)

        from_date = params.get("from_date")
        if from_date:
            filters &= Q(created_at__date__gte=from_date)

        to_date = params.get("to_date")
        if to_date:
            filters &= Q(created_at__date__lte=to_date)

        min_total = params.get("min_total")
        if min_total:
            filters &= Q(total_amount__gte=Decimal(min_total))

        max_total = params.get("max_total")
        if max_total:
            filters &= Q(total_amount__lte=Decimal(max_total))

        orders = Order.objects.filter(filters).select_related("customer")

        ordering = params.get("ordering", "-created_at")
        allowed_ordering = {
            "created_at",
            "-created_at",
            "total_amount",
            "-total_amount",
        }
        if ordering in allowed_ordering:
            secondary_ordering = "id" if not ordering.startswith("-") else "-id"
            return orders.order_by(ordering, secondary_ordering)

        return orders.order_by("-created_at", "-id")

    def get_for_business(self, business_id, order_id):
        return Order.objects.filter(
            business_id=business_id,
            pk=order_id,
        ).first()
