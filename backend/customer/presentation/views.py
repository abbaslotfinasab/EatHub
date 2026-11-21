from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from accounts.views import ExplicitTenantAPIView
from customer.infrastructure.django.customer_read_repository import (
    DjangoCustomerReadRepository,
)
from customer.presentation.serializers import (
    CreateCustomerSerializer,
    UpdateCustomerSerializer,
)
from customer.services.customer_service import CustomerService
from customer.presentation.read_serializers import (
    CustomerDetailReadSerializer,
    CustomerReadSerializer,
)


class CustomerListAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search", "").strip()
        balance = request.query_params.get("balance")
        min_orders_raw = request.query_params.get("minOrders")
        ordering = request.query_params.get("ordering", "-created_at")

        min_orders = None
        if min_orders_raw:
            try:
                min_orders = int(min_orders_raw)
            except ValueError:
                pass

        customers = DjangoCustomerReadRepository().list_for_business(
            request.business.id,
            search=search,
            balance=balance,
            min_orders=min_orders,
            ordering=ordering,
        )
        return Response(CustomerReadSerializer(customers, many=True).data)


class CustomerCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.create_customer(
            business=request.business,
            validated_data=serializer.validated_data,
        )
        return Response(CustomerReadSerializer(customer).data, status=status.HTTP_201_CREATED)


class CustomerDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        detail = DjangoCustomerReadRepository().get_detail_for_business(
            request.business.id, pk
        )
        if detail is None:
            raise NotFound()
        return Response(CustomerDetailReadSerializer(detail).data)


class CustomerUpdateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        customer = DjangoCustomerReadRepository().get_for_business(
            request.business.id, pk
        )
        if customer is None:
            raise NotFound()
        serializer = UpdateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerService.update_customer(
            customer=customer,
            validated_data=serializer.validated_data,
        )
        return Response(CustomerReadSerializer(customer).data)


class CustomerDeleteAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        customer = DjangoCustomerReadRepository().get_for_business(
            request.business.id, pk
        )
        if customer is None:
            raise NotFound()
        CustomerService.delete_customer(customer=customer)
        return Response(status=status.HTTP_204_NO_CONTENT)
