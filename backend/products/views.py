from django.forms import DecimalField
from rest_framework import status

from accounts.models import Business
from accounts.views import TenantAPIView
from products.serializers.customer_serializer import CustomerDetailSerializer, CustomerSerializer, \
    CreateCustomerSerializer, UpdateCustomerSerializer, CustomerTransactionSerializer, \
    CustomerAccountSerializer, CustomerListSerializer, CustomerBalanceSerializer
from products.serializers.order_serializer import *
from products.services.customer_service import CustomerService
from products.services.order_service import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from products.serializers.menu_serializer import CreateMenuWithItemsSerializer, MenuSerializer, \
    PublicRestaurantSerializer, PublicMenuSerializer, UpdateMenuSerializer, MenuItemSerializer, \
    MenuItemCreateSerializer, MenuItemUpdateSerializer
from products.services.menu_service import MenuService
from products.models import Menu, Customer, CustomerAccount
from inventory.services.facture_service import *
from products.services.wallet_service import WalletService
from django.db.models import (
    Q,
    Count,
    Sum,
    DecimalField,
    Value,
)
from django.db.models.functions import Coalesce




class MenuCreateAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CreateMenuWithItemsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        menu = MenuService.create_menu_with_items(
            business=request.business,
            validated_data=serializer.validated_data
        )

        return Response(
            MenuSerializer(menu).data,
            status=status.HTTP_201_CREATED
        )


class MenuListAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        menus = (
            Menu.objects
            .filter(business=request.business)
            .prefetch_related("items")
            .order_by("sort_order")
        )

        return Response(MenuSerializer(menus, many=True).data)


class MenuDetailAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        menu = get_object_or_404(
            Menu.objects.prefetch_related("items"),
            pk=pk,
            business=request.business
        )

        return Response(MenuSerializer(menu).data)



class MenuUpdateAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        menu = get_object_or_404(Menu, id=pk)

        serializer = UpdateMenuSerializer(
            menu,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        menu = MenuService.update_menu(
            menu,
            serializer.validated_data
        )

        return Response(MenuSerializer(menu).data)


class MenuDeleteAPIView(TenantAPIView):

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



class MenuItemCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, menu_id):

        menu = get_object_or_404(
            Menu,
            pk=menu_id,
            business=request.business,
        )
        serializer = MenuItemCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        item = MenuService.create_item(
            business=request.business,
            menu=menu,
            data=serializer.validated_data
        )

        return Response(
            MenuItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )

class MenuItemUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        serializer = MenuItemUpdateSerializer(
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        item = MenuService.update_item(
            serializer.validated_data
        )

        return Response(
            MenuItemSerializer(item).data
        )


class MenuItemDeleteAPIView(TenantAPIView):
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

class OrderCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = CreateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        order = OrderService.create_order(
            business=request.business,
            validated_data=serializer.validated_data
        )

        # PurchaseOrderService.create_from_order(order=order)

        return Response(
            OrderSerializer(order).data,
            status=201
        )


class OrderListAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = Order.objects.filter(
            business=request.business
        ).order_by("-id")

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


class OrderDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        order = Order.objects.get(
            id=pk,
            business=request.business
        )

        return Response(OrderSerializer(order).data)


class OrderStatusUpdateAPIView(TenantAPIView):

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


        order = OrderService.update_status(
            business=request.business,
            order_id=order_id,
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

class OrderUpdateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        serializer = UpdateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderService.update_order(
            business=request.business,
            order_id=pk,
            validated_data=serializer.validated_data,
        )

        return Response(OrderSerializer(order).data)


class OrderDeleteAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        order = get_object_or_404(
            Order,
            pk=pk,
            business=request.business,
        )

        OrderService.delete_order(order)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )



class CustomerListAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]


    def get(self, request):

        search = request.query_params.get(
            "search",
            "",
        ).strip()


        customers = Customer.objects.filter(
            business=request.business,
        )


        if search:

            customers = customers.filter(
                Q(name__icontains=search)
                |
                Q(phone__istartswith=search)
            )


        customers = customers.select_related(
            "account",
        ).annotate(

            total_orders=Count(
                "orders",
                distinct=True,
            ),


            total_spent=Coalesce(

                Sum(
                    "orders__total_amount",
                    filter=Q(
                        orders__status=Order.Status.COMPLETED
                    ),
                ),

                Value(0),

                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2,
                ),
            ),

        ).order_by(
            "-created_at",
        )


        serializer = CustomerListSerializer(
            customers,
            many=True,
        )


        return Response(
            serializer.data
        )


class CustomerCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CreateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = CustomerService.create_customer(
            business=request.business,
            validated_data=serializer.validated_data
        )

        return Response(CustomerSerializer(customer).data, status=201)



class CustomerDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        customer = get_object_or_404(
            Customer,
            id=pk,
            business=request.business
        )

        return Response(CustomerDetailSerializer(customer).data)



class CustomerUpdateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):

        customer = get_object_or_404(
            Customer,
            id=pk,
            business=request.business
        )

        serializer = UpdateCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = CustomerService.update_customer(
            customer=customer,
            validated_data=serializer.validated_data
        )

        return Response(CustomerSerializer(customer).data)

class CustomerDeleteAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        customer = get_object_or_404(
            Customer,
            id=pk,
            business=request.business
        )

        CustomerService.delete_customer(customer)

        return Response(status=204)



class CustomerAccountDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):

        account = get_object_or_404(
            CustomerAccount,
            customer_id=customer_id,
            business=request.business
        )

        return Response(CustomerAccountSerializer(account).data)



class CustomerCreditAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):

        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = get_object_or_404(
            Customer,
            id=customer_id,
            business=request.business
        )

        WalletService.credit(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get("description")
        )

        return Response({"status": "credited"})



class CustomerTransactionListAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):

        account = get_object_or_404(
            CustomerAccount,
            customer_id=customer_id,
            business=request.business
        )

        transactions = account.transactions.all().order_by("-id")

        return Response(CustomerTransactionSerializer(transactions, many=True).data)



class CustomerDebitAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):

        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = get_object_or_404(
            Customer,
            id=customer_id,
            business=request.business
        )

        WalletService.debit(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
        )

        return Response(
            {
                "status": "debited",
            }
        )


class CustomerAdjustAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, customer_id):

        serializer = CustomerBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = get_object_or_404(
            Customer,
            id=customer_id,
            business=request.business
        )

        WalletService.adjust(
            business=request.business,
            customer=customer,
            amount=serializer.validated_data["amount"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
        )

        return Response(
            {
                "status": "adjusted",
            }
        )