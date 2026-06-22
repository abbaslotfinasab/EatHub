from django.urls import path
from products.views import (
    MenuCreateAPIView,
    MenuListAPIView,
    MenuDetailAPIView,
    MenuDeleteAPIView, ImageUploadAPIView, PublicRestaurantMenuAPIView,
)

from products.views import (
    OrderCreateAPIView,
    OrderListAPIView,
    OrderStatusUpdateAPIView,
    OrderDetailAPIView
)

app_name = 'products'


urlpatterns = [
    # Create order
    path("orders/", OrderCreateAPIView.as_view(), name="order-create"),

    # List orders
    path("orders/list/", OrderListAPIView.as_view(), name="order-list"),

    # Order detail
    path("orders/<int:pk>/", OrderDetailAPIView.as_view(), name="order-detail"),

    # Update status (kitchen flow)
    path("orders/<int:pk>/status/", OrderStatusUpdateAPIView.as_view(), name="order-status-update"),

    path("menus/", MenuListAPIView.as_view(), name="menu-list"),
    path("menus/create/", MenuCreateAPIView.as_view(), name="menu-create"),
    path("menus/<int:pk>/", MenuDetailAPIView.as_view(), name="menu-detail"),
    path("menus/<int:pk>/delete/", MenuDeleteAPIView.as_view(), name="menu-delete"),

    path(
        "upload/image/",
        ImageUploadAPIView.as_view(),
        name="upload-image"
    ),

    path(
        "<str:slug>/menu/",
        PublicRestaurantMenuAPIView.as_view(),
        name="public-menu"
    ),
]