import json

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from accounts.models import Business
from products.serializers.image_serializer import ImageUploadSerializer
from products.serializers.order_serializer import *
from products.services.order_service import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from products.serializers.menu_serializer import CreateMenuWithItemsSerializer, MenuSerializer, \
    PublicRestaurantSerializer, PublicMenuSerializer
from products.services.menu_service import MenuService
from products.models import Menu


class MenuCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        data = request.data.copy()


        serializer = CreateMenuWithItemsSerializer(data=data)

        if not serializer.is_valid():
            print(serializer.errors)
            return Response(serializer.errors, status=400)

        memberships = request.user.memberships.filter(
            is_active=True
        ).select_related("business", "role")

        business = memberships.first()

        menu = MenuService.create_menu_with_items(
            business=business.business,
            validated_data=serializer.validated_data
        )

        return Response(MenuSerializer(menu).data, status=201)



class MenuListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = request.user.memberships.filter(
            is_active=True
        ).select_related("business", "role")

        business = memberships.first()

        menus = Menu.objects.filter(
            business=business.business
        ).order_by("sort_order")

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

class MenuDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        menu = Menu.objects.get(
            id=pk,
            business=request.business
        )

        return Response(MenuSerializer(menu).data)


class MenuDeleteAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        Menu.objects.filter(
            id=pk,
            business=request.business
        ).delete()

        return Response(status=204)

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