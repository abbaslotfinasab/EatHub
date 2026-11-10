from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.views import ExplicitTenantAPIView
from customer.models import Customer
from customer.presentation.serializers import (
    CreateCustomerSerializer,
    UpdateCustomerSerializer,
)
from customer.services.customer_service import CustomerService
from products.models import Order
# Transitional response serializers preserve the existing API payload while
# Financial read projections are extracted in a dedicated follow-up.
from products.serializers.customer_serializer import (
    CustomerDetailSerializer,
    CustomerSerializer,
)


class CustomerListAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        balance = request.query_params.get("balance")
        min_orders = request.query_params.get("minOrders")
        ordering = request.query_params.get("ordering", "-created_at")

        customers = Customer.objects.filter(business=request.business)

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

        if min_orders:
            try:
                customers = customers.filter(total_orders__gte=int(min_orders))
            except ValueError:
                pass

        if balance == "CREDITOR":
            customers = customers.filter(account__balance__gt=0)
        elif balance == "DEBTOR":
            customers = customers.filter(account__balance__lt=0)
        elif balance == "ZERO":
            customers = customers.filter(
                Q(account__balance=0) | Q(account__isnull=True)
            )

        allowed_ordering = {
            "-created_at", "created_at", "-total_spent", "-total_orders", "name"
        }
        customers = customers.order_by(
            ordering if ordering in allowed_ordering else "-created_at"
        )
        return Response(CustomerSerializer(customers, many=True).data)


class CustomerCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.create_customer(
            business=request.business,
            validated_data=serializer.validated_data,
        )
        return Response(CustomerSerializer(customer).data, status=status.HTTP_201_CREATED)


class CustomerDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        customer = get_object_or_404(
            Customer.objects.filter(business=request.business)
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
            ),
            id=pk,
        )
        return Response(CustomerDetailSerializer(customer).data)


class CustomerUpdateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        customer = get_object_or_404(
            Customer, id=pk, business=request.business
        )
        serializer = UpdateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.update_customer(
            customer=customer,
            validated_data=serializer.validated_data,
        )
        return Response(CustomerSerializer(customer).data)


class CustomerDeleteAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        customer = get_object_or_404(
            Customer, id=pk, business=request.business
        )
        CustomerService.delete_customer(customer=customer)
        return Response(status=status.HTTP_204_NO_CONTENT)
