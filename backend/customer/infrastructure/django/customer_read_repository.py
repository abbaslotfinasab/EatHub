"""Django-backed read queries for the Customer API."""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from customer.models import Customer
from products.models import Order


class DjangoCustomerReadRepository:
    """Own Customer read-side ORM access outside the Presentation layer."""

    def list_for_business(
        self, business_id, *, search="", balance=None, min_orders=None, ordering="-created_at"
    ):
        customers = Customer.objects.filter(business_id=business_id)
        if search:
            customers = customers.filter(
                Q(name__icontains=search) | Q(phone__istartswith=search)
            )

        customers = customers.select_related("account").annotate(
            total_orders=Count("orders", distinct=True),
            total_spent=Coalesce(
                Sum(
                    "orders__total_amount",
                    filter=Q(orders__status=Order.Status.COMPLETED),
                ),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        if min_orders is not None:
            customers = customers.filter(total_orders__gte=min_orders)

        if balance == "CREDITOR":
            customers = customers.filter(account__balance__gt=0)
        elif balance == "DEBTOR":
            customers = customers.filter(account__balance__lt=0)
        elif balance == "ZERO":
            customers = customers.filter(Q(account__balance=0) | Q(account__isnull=True))

        allowed_ordering = {
            "-created_at", "created_at", "-total_spent", "-total_orders", "name"
        }
        return customers.order_by(
            ordering if ordering in allowed_ordering else "-created_at"
        )

    def get_for_business(self, business_id, customer_id):
        return (
            Customer.objects.filter(business_id=business_id)
            .select_related("account")
            .filter(pk=customer_id)
            .first()
        )

    def get_detail_for_business(self, business_id, customer_id):
        customer = (
            Customer.objects.filter(business_id=business_id)
            .select_related("account")
            .annotate(
                total_orders=Count(
                    "orders",
                    filter=Q(orders__status=Order.Status.COMPLETED),
                    distinct=True,
                ),
                total_spent=Coalesce(
                    Sum(
                        "orders__total_amount",
                        filter=Q(orders__status=Order.Status.COMPLETED),
                    ),
                    Value(0),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            )
            .filter(pk=customer_id)
            .first()
        )
        if customer is None:
            return None
        try:
            account = customer.account
        except ObjectDoesNotExist:
            account = None
        transactions = (
            account.transactions.all().order_by("-created_at", "-id")
            if account is not None
            else []
        )
        return {"customer": customer, "account": account, "transactions": transactions}
