"""Backward-compatible imports for Customer presentation serializers.

Customer owns the customer API read contract. Keep these aliases while legacy
callers migrate away from the Products namespace.
"""

from customer.presentation.read_serializers import (
    CreateCustomerSerializer,
    UpdateCustomerSerializer,
    CustomerReadSerializer as CustomerSerializer,
    CustomerDetailReadSerializer as CustomerDetailSerializer,
)
