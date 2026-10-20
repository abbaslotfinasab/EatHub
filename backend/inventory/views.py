from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from inventory.application.dto.stock_balance import ListStockBalancesQuery
from inventory.application.use_cases.list_stock_balances import (
    ListStockBalancesUseCase,
)
from inventory.domain.value_objects.unit import Unit
from inventory.infrastructure.django.repositories import (
    DjangoIngredientRepository,
    DjangoStockBalanceRepository,
    DjangoWarehouseRepository,
)


class StockBalanceQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(
        min_value=1, max_value=100, required=False, default=20
    )
    ingredient_id = serializers.IntegerField(min_value=1, required=False)
    warehouse_id = serializers.IntegerField(min_value=1, required=False)


class StockBalanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    ingredient_id = serializers.IntegerField()
    ingredient_name = serializers.CharField()
    warehouse_id = serializers.IntegerField()
    warehouse_name = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=36, decimal_places=12)
    unit = serializers.ChoiceField(choices=[unit.value for unit in Unit])
    average_cost = serializers.DecimalField(max_digits=70, decimal_places=48)


class StockBalancePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    results = StockBalanceSerializer(many=True)


class StockBalanceListAPIView(TenantAPIView):
    """GET /api/inventory/balances/.

    Query parameters are ``page`` (default 1), ``page_size`` (default 20,
    maximum 100), and optional positive ``ingredient_id``/``warehouse_id``.
    The response is ``{count, page, page_size, results}``; each result has
    ``id``, ingredient/warehouse IDs and names, Decimal-string ``quantity``
    and ``average_cost``, and canonical ``unit``. Pages beyond the last page
    return an empty ``results`` array with the requested page metadata.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query_serializer = StockBalanceQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        values = query_serializer.validated_data

        use_case = ListStockBalancesUseCase(
            DjangoStockBalanceRepository(),
            DjangoIngredientRepository(),
            DjangoWarehouseRepository(),
        )
        try:
            page = use_case.execute(
                ListStockBalancesQuery(
                    business_id=request.business.id,
                    page=values["page"],
                    page_size=values["page_size"],
                    ingredient_id=values.get("ingredient_id"),
                    warehouse_id=values.get("warehouse_id"),
                )
            )
        except ValueError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error

        response_serializer = StockBalancePageSerializer(page)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
