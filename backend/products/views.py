
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import status

from accounts.models import Business
from accounts.views import TenantAPIView
from products.serializers.image_serializer import ImageUploadSerializer
from products.serializers.order_serializer import *
from products.services.order_service import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from products.serializers.menu_serializer import CreateMenuWithItemsSerializer, MenuSerializer, \
    PublicRestaurantSerializer, PublicMenuSerializer, UpdateMenuSerializer, MenuItemSerializer, \
    MenuItemCreateSerializer, MenuItemUpdateSerializer
from products.services.menu_service import MenuService
from products.models import Menu


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

class MenuDetailAPIView(TenantAPIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        menu = get_object_or_404(
            Menu.objects.prefetch_related("items"),
            pk=pk,
            business=request.business
        )

        return Response(MenuSerializer(menu).data)



class MenuUpdateAPIView(APIView):

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


class MenuDeleteAPIView(APIView):

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

class MenuItemCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, menu_id):

        menu = get_object_or_404(
            Menu.objects.filter(
                business=request.business
            ),
            pk=menu_id
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


class MenuItemDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        item = get_object_or_404(
            MenuItem.objects.select_related(
                "menu"
            ),
            pk=pk,
            menu__business=request.business
        )

        MenuService.delete_item(item)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = CreateOrderInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderService.create_order(
            business=request.business,
            validated_data=serializer.validated_data
        )

        return Response(
            OrderSerializer(order).data,
            status=201
        )


class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = Order.objects.filter(
            business=request.business
        ).order_by("-id")

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        order = Order.objects.get(
            id=pk,
            business=request.business
        )

        return Response(OrderSerializer(order).data)


class OrderStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        order = Order.objects.get(
            id=pk,
            business=request.business
        )

        new_status = request.data.get("status")

        order.status = new_status
        order.save()

        return Response({"status": "updated"})


class ImageUploadAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]

        path = default_storage.save(
            f"menu-items/{file.name}",
            file
        )

        return Response({
            "url": request.build_absolute_uri(
                default_storage.url(path)
            )
        })