from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import ExplicitTenantAPIView
from catalog.application.exceptions import ProductNotFound, ProductSkuConflict
from catalog.bootstrap import create_product, get_product, list_products, update_product
from catalog.presentation.serializers import (
    ProductCreateSerializer,
    ProductQuerySerializer,
    ProductSerializer,
    ProductUpdateSerializer,
)
from core.enums import PermissionCode


def _require_permission(request, permission):
    if permission.value not in request.permissions:
        raise PermissionDenied("You do not have permission to manage the Product Catalog.")


def _translate_write_error(error):
    if isinstance(error, ProductSkuConflict):
        raise ValidationError({"sku": "This SKU is already used in this business."}) from error
    if isinstance(error, ProductNotFound):
        raise NotFound("Product does not exist in this business.") from error
    raise error


class ProductListCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(request, PermissionCode.PRODUCTS_VIEW)
        query = ProductQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        result = list_products(
            business_id=request.business.pk,
            page=params["page"],
            page_size=params["page_size"],
            search=params.get("search"),
            category=params.get("category"),
            status=params.get("status"),
        )
        return Response({
            "count": result["count"],
            "page": result["page"],
            "page_size": result["page_size"],
            "results": ProductSerializer(result["results"], many=True).data,
        })

    def post(self, request):
        _require_permission(request, PermissionCode.PRODUCTS_CREATE)
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            product = create_product(
                business_id=request.business.pk,
                data=serializer.validated_data,
            )
        except (ProductSkuConflict, ProductNotFound) as error:
            _translate_write_error(error)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(request, PermissionCode.PRODUCTS_VIEW)
        try:
            product = get_product(
                business_id=request.business.pk,
                product_id=pk,
            )
        except ProductNotFound as error:
            raise NotFound("Product does not exist in this business.") from error
        return Response(ProductSerializer(product).data)

    def patch(self, request, pk):
        _require_permission(request, PermissionCode.PRODUCTS_UPDATE)
        serializer = ProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            product = update_product(
                business_id=request.business.pk,
                product_id=pk,
                data=serializer.validated_data,
            )
        except (ProductSkuConflict, ProductNotFound) as error:
            _translate_write_error(error)
        product = get_product(
            business_id=request.business.pk,
            product_id=product.pk,
        )
        return Response(ProductSerializer(product).data)
