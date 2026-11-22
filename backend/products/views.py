from django.forms import DecimalField
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status

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
from products.infrastructure.django.menu_read_repository import DjangoMenuReadRepository
from products.infrastructure.django.menu_write_repository import DjangoMenuWriteRepository
from products.infrastructure.django.order_read_repository import DjangoOrderReadRepository
from products.infrastructure.django.order_refund_read_repository import DjangoOrderRefundReadRepository
from products.services.order_inventory_service import OrderInventoryService
from products.models import (
    Customer,
    Order,
    OrderStatusHistory,
    OrderPaymentEvent,
)
from django.db.models import (
    Q,
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
            menu = DjangoMenuWriteRepository().get_menu_with_items_for_business(
                request.business.id, menu.pk,
            )
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

        menus = DjangoMenuReadRepository().list_for_business(
            request.business.id
        )

        return Response(MenuSerializer(menus, many=True).data)


class MenuDetailAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        menu = DjangoMenuReadRepository().get_for_business(
            request.business.id, pk
        )
        if menu is None:
            raise Http404

        return Response(MenuSerializer(menu).data)



class MenuUpdateAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        menu = DjangoMenuWriteRepository().get_menu_for_business(request.business.id, pk)
        if menu is None:
            raise Http404

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
            menu = DjangoMenuWriteRepository().get_menu_with_items_for_business(
                request.business.id, menu.pk,
            )
        except IntegrityError as error:
            raise ValidationError({
                "recipe_id": "A recipe can only be assigned to one menu item."
            }) from error

        return Response(MenuSerializer(menu).data)


class MenuDeleteAPIView(ExplicitTenantAPIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        menu = DjangoMenuWriteRepository().get_menu_for_business(request.business.id, pk)
        if menu is None:
            raise Http404

        MenuService.delete_menu(menu)

        return Response(
            status=204
        )



class PublicRestaurantMenuAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, slug):
        repository = DjangoMenuReadRepository()
        business = repository.get_active_business_by_slug(slug)
        if business is None:
            raise Http404

        menus = repository.list_public_for_business(business.id)

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

        menu = DjangoMenuWriteRepository().get_menu_for_business(request.business.id, menu_id)
        if menu is None:
            raise Http404
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
        item = DjangoMenuWriteRepository().get_menu_item_for_business(request.business.id, pk)
        if item is None:
            raise Http404
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

        item = DjangoMenuWriteRepository().get_menu_item_for_menu_business(request.business.id, pk)
        if item is None:
            raise Http404

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_permission(
            request,
            PermissionCode.ORDERS_VIEW,
            "You do not have permission to view orders.",
        )
        orders = DjangoOrderReadRepository().list_for_business(
            request.business.id,
            request.query_params,
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
        order = DjangoOrderReadRepository().get_for_business(
            request.business.id,
            pk,
        )
        if order is None:
            raise Http404
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
        repository = DjangoOrderReadRepository()
        order = repository.get_for_business(request.business.id, order_id)
        if order is None:
            raise Http404
        history = repository.list_status_history_for_business(
            request.business.id, order.pk,
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


class OrderPaymentEventListAPIView(ExplicitTenantAPIView):
    """Return immutable, tenant-scoped financial events for an order."""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        _require_financial_access(
            request, "You do not have permission to view order payment history."
        )
        repository = DjangoOrderReadRepository()
        order = repository.get_for_business(request.business.id, order_id)
        if order is None:
            raise Http404
        events = repository.list_payment_events_for_business(
            request.business.id, order.pk,
        )
        response = Response({
            "order_id": order.pk,
            "events": [
                {
                    "id": event.pk,
                    "event_type": event.event_type,
                    "from_payment_status": event.from_payment_status,
                    "to_payment_status": event.to_payment_status,
                    "from_payment_method": event.from_payment_method,
                    "to_payment_method": event.to_payment_method,
                    "from_total_amount": (
                        str(event.from_total_amount) if event.from_total_amount is not None else None
                    ),
                    "to_total_amount": (
                        str(event.to_total_amount) if event.to_total_amount is not None else None
                    ),
                    "metadata": event.metadata,
                    "actor": (
                        {"id": event.actor_id, "name": event.actor.name}
                        if event.actor_id else None
                    ),
                    "created_at": event.created_at,
                }
                for event in events
            ],
        })
        response["Cache-Control"] = "no-store"
        return response



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

        repository = DjangoOrderReadRepository()
        order = repository.get_for_business(request.business.id, order_id)
        if order is None:
            raise Http404
        requirements = list(
            repository.list_consumption_requirements_for_order(
                request.business.id, order.pk,
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

        actual_totals = repository.summarize_actual_consumption_for_order(
            request.business.id,
            order.pk,
            [item.pk for item in requirements],
        )
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
            order, refunds = DjangoOrderRefundReadRepository().get_recovery_state_for_business(
                request.business.id, order_id,
            )
            if (
                order is None
                or order.payment_status != Order.PaymentStatus.REFUNDED
                or not refunds
            ):
                raise Http404("No completed refund exists for this order.")
            if len(refunds) != 1:
                raise ValidationError(
                    "Multiple refund records exist for this order; review its financial history."
                )
            refund = refunds[0]
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




