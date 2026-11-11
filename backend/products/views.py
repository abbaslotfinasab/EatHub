from django.forms import DecimalField
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status

from accounts.models import Business
from accounts.views import ExplicitTenantAPIView, TenantAPIView
from products.serializers.order_serializer import *
from products.services.order_service import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from core.enums import PermissionCode
from inventory.application.exceptions import OperationConflict, ResourceNotFound
from products.serializers.menu_serializer import CreateMenuWithItemsSerializer, MenuSerializer, \
    PublicRestaurantSerializer, PublicMenuSerializer, UpdateMenuSerializer, MenuItemSerializer, \
    MenuItemCreateSerializer, MenuItemUpdateSerializer
from products.services.menu_service import MenuService
from products.services.order_inventory_service import OrderInventoryService
from products.models import (
    Menu,
    MenuItem,
    Customer,
    Order,
    OrderStatusHistory,
    OrderRefund,
    OrderItemIngredientRequirement,
    OrderInventoryConsumptionLine,
)
from django.db.models import (
    Q,
    Count,
    Sum,
    DecimalField,
    Value,
)
from django.db.models.functions import Coalesce
from products.pagination import OrderListPagination


FINANCIAL_ROLE_CODES = {"OWNER", "MANAGER", "ACCOUNTANT"}


def _require_permission(request, permission, message):
    if permission not in request.permissions:
        raise PermissionDenied(message)


def _require_financial_access(request, message):
    role = getattr(request, "role", None)
    if (
        role is None
        or role.code not in FINANCIAL_ROLE_CODES
        or PermissionCode.PAYMENTS_MANAGE not in request.permissions
    ):
        raise PermissionDenied(message)



class MenuCreateAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CreateMenuWithItemsSerializer(
            data=request.data, context={"business": request.business}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            menu = MenuService.create_menu_with_items(
                business=request.business,
                validated_data=serializer.validated_data
            )
            menu = Menu.objects.prefetch_related("items__product").get(pk=menu.pk)
        except IntegrityError as error:
            raise ValidationError({
                "recipe_id": "A recipe can only be assigned to one menu item."
            }) from error

        return Response(
            MenuSerializer(menu).data,
            status=status.HTTP_201_CREATED
        )


class MenuListAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        menus = (
            Menu.objects
            .filter(business=request.business)
            .prefetch_related("items__product")
            .order_by("sort_order")
        )

        return Response(MenuSerializer(menus, many=True).data)


class MenuDetailAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        menu = get_object_or_404(
            Menu.objects.prefetch_related("items__product"),
            pk=pk,
            business=request.business
        )

        return Response(MenuSerializer(menu).data)



class MenuUpdateAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        menu = get_object_or_404(Menu, id=pk, business=request.business)

        serializer = UpdateMenuSerializer(
            menu,
            data=request.data,
            partial=True,
            context={"business": request.business},
        )
        serializer.is_valid(raise_exception=True)

        try:
            menu = MenuService.update_menu(
                menu,
                serializer.validated_data
            )
            menu = Menu.objects.prefetch_related("items__product").get(pk=menu.pk)
        except IntegrityError as error:
            raise ValidationError({
                "recipe_id": "A recipe can only be assigned to one menu item."
            }) from error

        return Response(MenuSerializer(menu).data)


class MenuDeleteAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        menu = get_object_or_404(
            Menu,
            pk=pk,
            business=request.business
        )

        MenuService.delete_menu(menu)

        return Response(
            status=204
        )



class PublicRestaurantMenuAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, slug):
        business = get_object_or_404(
            Business,
            slug=slug,
            is_active=True,
        )

        menus = (
            Menu.objects
            .filter(
                business=business
            )
            .prefetch_related(
                "items"
            )
            .order_by(
                "sort_order"
            )
        )

        return Response({
            "restaurant":
                PublicRestaurantSerializer(
                    business
                ).data,

            "menus":
                PublicMenuSerializer(
                    menus,
                    many=True
                ).data,
        })



class MenuItemCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, menu_id):

        menu = get_object_or_404(
            Menu,
            pk=menu_id,
            business=request.business,
        )
        serializer = MenuItemCreateSerializer(
            data=request.data,
            context={"business": request.business},
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            item = MenuService.create_item(
                business=request.business,
                menu=menu,
                data=serializer.validated_data
            )
        except IntegrityError as error:
            raise ValidationError({
                "recipe_id": "A recipe can only be assigned to one menu item."
            }) from error

        return Response(
            MenuItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )

class MenuItemUpdateAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        item = get_object_or_404(
            MenuItem.objects.select_related("product"),
            pk=pk,
            business=request.business,
        )
        serializer = MenuItemUpdateSerializer(
            data=request.data,
            partial=True,
            context={"business": request.business},
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            item = MenuService.update_item(
                item,
                serializer.validated_data,
            )
        except IntegrityError as error:
            raise ValidationError({
                "recipe_id": "A recipe can only be assigned to one menu item."
            }) from error

        return Response(
            MenuItemSerializer(item).data
        )


class MenuItemDeleteAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        item = get_object_or_404(
            MenuItem,
            pk=pk,
            menu__business=request.business,
        )

        MenuService.delete_item(item)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class OrderCreateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        _require_permission(
            request,
            PermissionCode.ORDERS_CREATE,
            "You do not have permission to create orders.",
        )

        serializer = CreateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        order = OrderService.create_order(
            business=request.business,
            validated_data=serializer.validated_data,
            user=request.user,
            idempotency_key=serializer.validated_data["idempotency_key"],
        )

        return Response(
            OrderSerializer(order).data,
            status=201
        )



class OrderListAPIView(ExplicitTenantAPIView):

    permission_classes = [
        IsAuthenticated
    ]


    def get(self, request):
        _require_permission(
            request,
            PermissionCode.ORDERS_VIEW,
            "You do not have permission to view orders.",
        )

        filters = Q(
            business=request.business
        )


        # =========================
        # Search
        # =========================

        search = request.query_params.get(
            "search",
            ""
        ).strip()


        if search:

            filters &= (

                Q(
                    id__icontains=search
                )
                |
                Q(
                    customer__name__icontains=search
                )
                |
                Q(
                    customer__phone__icontains=search
                )

            )



        # =========================
        # Status
        # =========================

        status = request.query_params.get(
            "status"
        )


        if status:

            filters &= Q(
                status=status
            )



        # =========================
        # Order Type
        # =========================

        order_type = request.query_params.get(
            "order_type"
        )


        if order_type:

            filters &= Q(
                order_type=order_type
            )



        # =========================
        # Payment Status
        # =========================

        payment_status = request.query_params.get(
            "payment_status"
        )


        if payment_status:

            filters &= Q(
                payment_status=payment_status
            )



        # =========================
        # Payment Method
        # =========================

        payment_method = request.query_params.get(
            "payment_method"
        )


        if payment_method:

            filters &= Q(
                payment_method=payment_method
            )



        # =========================
        # Date Range
        # =========================

        from_date = request.query_params.get(
            "from_date"
        )


        to_date = request.query_params.get(
            "to_date"
        )


        if from_date:

            filters &= Q(
                created_at__date__gte=from_date
            )


        if to_date:

            filters &= Q(
                created_at__date__lte=to_date
            )



        # =========================
        # Amount
        # =========================

        min_total = request.query_params.get(
            "min_total"
        )


        max_total = request.query_params.get(
            "max_total"
        )


        if min_total:

            filters &= Q(
                total_amount__gte=Decimal(min_total)
            )


        if max_total:

            filters &= Q(
                total_amount__lte=Decimal(max_total)
            )



        # =========================
        # Query
        # =========================

        orders = (

            Order.objects
            .filter(filters)
            .select_related(
                "customer",
            )

        )



        # =========================
        # Ordering
        # =========================

        ordering = request.query_params.get(
            "ordering",
            "-created_at"
        )


        allowed_ordering = {

            "created_at",
            "-created_at",

            "total_amount",
            "-total_amount",

        }


        if ordering in allowed_ordering:

            secondary_ordering = "id" if not ordering.startswith("-") else "-id"
            orders = orders.order_by(
                ordering,
                secondary_ordering,
            )

        else:

            orders = orders.order_by(
                "-created_at",
                "-id",
            )



        paginator = OrderListPagination()
        page = paginator.paginate_queryset(orders, request, view=self)
        serializer = OrderSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
class OrderDetailAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _require_permission(
            request,
            PermissionCode.ORDERS_VIEW,
            "You do not have permission to view orders.",
        )
        order = get_object_or_404(
            Order,
            id=pk,
            business=request.business,
        )

        return Response(OrderSerializer(order).data)


class OrderStatusUpdateAPIView(ExplicitTenantAPIView):

    permission_classes = [
        IsAuthenticated
    ]

    def patch(
        self,
        request,
        order_id,
    ):

        serializer = OrderStatusUpdateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )
        changes = serializer.validated_data
        if "status" in changes:
            _require_permission(
                request,
                PermissionCode.ORDERS_UPDATE,
                "You do not have permission to update orders.",
            )
        if changes.get("status") == Order.Status.CANCELLED:
            _require_permission(
                request,
                PermissionCode.ORDERS_CANCEL,
                "You do not have permission to cancel orders.",
            )
        if changes.get("status") in {
            Order.Status.CONFIRMED,
            Order.Status.READY,
            Order.Status.CANCELLED,
            Order.Status.FAILED,
        }:
            _require_permission(
                request,
                PermissionCode.INVENTORY_ORDER_FULFILL,
                "You do not have permission to fulfill order inventory.",
            )
        if {"payment_status", "payment_method"}.intersection(changes):
            _require_financial_access(
                request, "You do not have permission to manage order payments."
            )


        order = OrderService.update_status(
            business=request.business,
            order_id=order_id,
            user=request.user,
            **serializer.validated_data,
        )


        return Response(
            {
                "id": order.id,
                "status": order.status,
                "payment_status": order.payment_status,
                "payment_method": order.payment_method,
            }
        )


class OrderStatusHistoryAPIView(ExplicitTenantAPIView):
    """Return the chronological, tenant-scoped status history for an order."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        _require_permission(
            request,
            PermissionCode.ORDERS_VIEW,
            "You do not have permission to view orders.",
        )
        order = get_object_or_404(
            Order.objects.filter(business=request.business),
            pk=order_id,
        )
        history = (
            OrderStatusHistory.objects
            .filter(business=request.business, order=order)
            .select_related("actor")
            .order_by("created_at", "pk")
        )
        return Response({
            "order_id": order.pk,
            "history": [
                {
                    "id": entry.pk,
                    "from_status": entry.from_status,
                    "to_status": entry.to_status,
                    "actor": (
                        {"id": entry.actor_id, "name": entry.actor.name}
                        if entry.actor_id else None
                    ),
                    "created_at": entry.created_at,
                }
                for entry in history
            ],
        })


class OrderActualConsumptionAPIView(ExplicitTenantAPIView):
    """Record operator-entered actual use for a preparing, tenant-scoped order."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        _require_permission(
            request,
            PermissionCode.ORDERS_VIEW,
            "You do not have permission to view orders.",
        )
        _require_permission(
            request,
            PermissionCode.INVENTORY_ORDER_FULFILL,
            "You do not have permission to view order inventory requirements.",
        )

        order = get_object_or_404(
            Order.objects.filter(business=request.business), pk=order_id,
        )
        requirements = list(
            OrderItemIngredientRequirement.objects.filter(
                snapshot__business_id=request.business.id,
                snapshot__order_id=order.pk,
                snapshot__order__business_id=request.business.id,
            ).select_related("snapshot__order_item").order_by(
                "snapshot__order_item_id", "pk",
            )
        )
        ingredient_ids = {item.ingredient_id for item in requirements}
        ingredients = {}
        if ingredient_ids:
            try:
                ingredient_rows = OrderInventoryService.resolve_requirement_ingredients(
                    business_id=request.business.id,
                    ingredient_ids=sorted(ingredient_ids),
                )
            except ResourceNotFound as error:
                raise Http404("An order requirement was not found in this business.") from error
            ingredients = {ingredient.id: ingredient for ingredient in ingredient_rows}

        actual_totals = {
            row["requirement_id"]: {
                "quantity": row["total"] or 0,
                "count": row["entries"],
            }
            for row in OrderInventoryConsumptionLine.objects.filter(
                consumption__business_id=request.business.id,
                consumption__order_id=order.pk,
                requirement_id__in=[item.pk for item in requirements],
            ).values("requirement_id").annotate(
                total=Sum("actual_quantity"),
                entries=Count("pk"),
            )
        }
        return Response({
            "order_id": order.pk,
            "requirements": [
                {
                    "requirement_id": item.pk,
                    "order_item_id": item.snapshot.order_item_id,
                    "menu_item_name": item.snapshot.order_item.menu_item_name,
                    "ingredient_id": item.ingredient_id,
                    "ingredient_name": ingredients[item.ingredient_id].name,
                    "standard_quantity": format(item.standard_quantity, "f"),
                    "actual_quantity": format(
                        actual_totals.get(item.pk, {}).get("quantity", 0), "f",
                    ),
                    "unit": item.unit,
                    "has_actual_record": item.pk in actual_totals,
                }
                for item in requirements
            ],
        })

    def post(self, request, order_id):
        if PermissionCode.ORDERS_UPDATE not in request.permissions:
            raise PermissionDenied("You do not have permission to update orders.")
        if PermissionCode.INVENTORY_ORDER_FULFILL not in request.permissions:
            raise PermissionDenied("You do not have permission to post inventory consumption.")
        serializer = OrderActualConsumptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            event = OrderInventoryService.record_consumption(
                business_id=request.business.id,
                order_id=order_id,
                actor_id=request.user.pk,
                idempotency_key=serializer.validated_data["idempotency_key"],
                lines=[
                    {**line, "quantity": str(line["quantity"])}
                    for line in serializer.validated_data["lines"]
                ],
            )
        except ResourceNotFound as error:
            raise Http404(str(error)) from error
        except OperationConflict as error:
            raise ValidationError({"detail": str(error)}) from error
        return Response({
            "id": event.pk,
            "order_id": event.order_id,
            "idempotency_key": str(event.idempotency_key),
            "created_at": event.created_at,
            "inventory_operation_id": event.inventory_operation_id,
            "lines": [
                {
                    "requirement_id": line.requirement_id,
                    "order_item_id": line.requirement.snapshot.order_item_id,
                    "ingredient_id": line.requirement.ingredient_id,
                    "actual_quantity": str(line.actual_quantity),
                    "unit": line.unit,
                    "movement_id": line.inventory_movement_id,
                }
                for line in event.lines.select_related(
                    "requirement__snapshot__order_item", "requirement__ingredient", "inventory_movement"
                ).order_by("pk")
            ],
        }, status=status.HTTP_201_CREATED)


class OrderRefundAPIView(ExplicitTenantAPIView):
    """Create full refunds and recover the committed refund receipt by order.

    GET is a durable recovery path after a lost POST response. It returns only
    the tenant-scoped completed refund, and takes the order lock so an
    in-flight refund is resolved before absence is reported.
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _refund_response(refund):
        return {
            "id": refund.id,
            "order_id": refund.order_id,
            "payment_method": refund.payment_method,
            "amount": refund.amount,
            "reason": refund.reason,
            "reference": refund.reference,
            "created_at": refund.created_at,
            "idempotency_key": refund.idempotency_key,
            "status": Order.PaymentStatus.REFUNDED,
        }

    def get(self, request, order_id):
        _require_financial_access(request, "You do not have permission to view refunds.")

        # Acquiring the same order lock as refund_order makes a recovery lookup
        # wait for an in-flight refund transaction before deciding it is absent.
        with transaction.atomic():
            order = get_object_or_404(
                Order.objects.select_for_update(),
                id=order_id,
                business=request.business,
            )
            refunds = OrderRefund.objects.filter(
                order=order,
                business=request.business,
            )
            if order.payment_status != Order.PaymentStatus.REFUNDED or not refunds.exists():
                raise Http404("No completed refund exists for this order.")
            if refunds.count() != 1:
                raise ValidationError(
                    "Multiple refund records exist for this order; review its financial history."
                )
            refund = refunds.first()
            response = Response(self._refund_response(refund))
            response["Cache-Control"] = "no-store"
            return response

    def post(self, request, order_id):
        _require_financial_access(request, "You do not have permission to manage refunds.")

        serializer = OrderRefundInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = OrderService.refund_order(
            business=request.business,
            order_id=order_id,
            user=request.user,
            **serializer.validated_data,
        )
        response = Response(
            self._refund_response(refund), status=status.HTTP_200_OK
        )
        response["Cache-Control"] = "no-store"
        return response

class OrderUpdateAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if PermissionCode.ORDERS_UPDATE not in request.permissions:
            raise PermissionDenied("You do not have permission to update orders.")

        serializer = UpdateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if {"customer", "items", "discount", "tax"}.intersection(serializer.validated_data):
            _require_financial_access(
                request, "You do not have permission to change order financials."
            )

        order = OrderService.update_order(
            business=request.business,
            order_id=pk,
            validated_data=serializer.validated_data,
            user=request.user,
        )

        return Response(OrderSerializer(order).data)


class OrderDeleteAPIView(ExplicitTenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        _require_permission(
            request,
            PermissionCode.ORDERS_DELETE,
            "You do not have permission to delete orders.",
        )

        order = get_object_or_404(
            Order,
            pk=pk,
            business=request.business,
        )

        OrderService.delete_order(order, user=request.user)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )




