from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import ExplicitTenantAPIView
from catalog.application.services import ProductCatalogService
from catalog.models import Product
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


class ProductListCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(request, PermissionCode.PRODUCTS_VIEW)
        query = ProductQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        products = Product.objects.filter(business=request.business).prefetch_related("allergen_declarations", "dietary_tags")
        if params.get("search"):
            term = params["search"].strip()
            products = products.filter(Q(name__icontains=term) | Q(sku__icontains=term))
        if params.get("category"):
            products = products.filter(category__iexact=params["category"].strip())
        if params.get("status"):
            products = products.filter(status=params["status"])
        count = products.count()
        start = (params["page"] - 1) * params["page_size"]
        results = products.order_by("name", "id")[start:start + params["page_size"]]
        return Response({
            "count": count,
            "page": params["page"],
            "page_size": params["page_size"],
            "results": ProductSerializer(results, many=True).data,
        })

    def post(self, request):
        _require_permission(request, PermissionCode.PRODUCTS_CREATE)
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = ProductCatalogService.create(
            business=request.business,
            validated_data=serializer.validated_data,
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(request, PermissionCode.PRODUCTS_VIEW)
        product = Product.objects.filter(business=request.business, pk=pk).prefetch_related("allergen_declarations", "dietary_tags").first()
        if product is None:
            raise NotFound("Product does not exist in this business.")
        return Response(ProductSerializer(product).data)

    def patch(self, request, pk):
        _require_permission(request, PermissionCode.PRODUCTS_UPDATE)
        product = Product.objects.filter(business=request.business, pk=pk).first()
        if product is None:
            raise NotFound("Product does not exist in this business.")
        serializer = ProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = ProductCatalogService.update(
            product=product,
            validated_data=serializer.validated_data,
        )
        return Response(ProductSerializer(product).data)
