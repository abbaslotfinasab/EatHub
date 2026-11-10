"""Backward-compatible imports for Customer presentation serializers."""

from customer.presentation.read_serializers import (
    CustomerReadSerializer as CustomerSerializer,
    CustomerDetailReadSerializer as CustomerDetailSerializer,
)
from customer.presentation.serializers import (
    CreateCustomerSerializer,
    UpdateCustomerSerializer,
)
