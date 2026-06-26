from django.urls import path

from products.views import (
    MenuCreateAPIView,
    MenuListAPIView,
    MenuDetailAPIView,
    MenuUpdateAPIView,
    MenuDeleteAPIView,

    MenuItemCreateAPIView,
    MenuItemUpdateAPIView,
    MenuItemDeleteAPIView,

    ImageUploadAPIView,
    PublicRestaurantMenuAPIView,

    OrderCreateAPIView,
    OrderListAPIView,
    OrderDetailAPIView,
    OrderStatusUpdateAPIView,
)

app_name = "products"

urlpatterns = [
    # ==========================
    # Public Menu
    # ==========================
    path(
        "<slug:slug>/menu/",
        PublicRestaurantMenuAPIView.as_view(),
        name="public-menu",
    ),

    # ==========================
    # Image
    # ==========================
    path(
        "upload/image/",
        ImageUploadAPIView.as_view(),
        name="upload-image",
    ),

    # ==========================
    # Menus
    # ==========================
    path(
        "menus/",
        MenuListAPIView.as_view(),
        name="menu-list",
    ),
    path(
        "menus/create/",
        MenuCreateAPIView.as_view(),
        name="menu-create",
    ),
    path(
        "menus/<int:pk>/",
        MenuDetailAPIView.as_view(),
        name="menu-detail",
    ),
    path(
        "menus/<int:pk>/update/",
        MenuUpdateAPIView.as_view(),
        name="menu-update",
    ),
    path(
        "menus/<int:pk>/delete/",
        MenuDeleteAPIView.as_view(),
        name="menu-delete",
    ),

    # ==========================
    # Menu Items
    # ==========================
    path(
        "menus/<int:menu_id>/items/create/",
        MenuItemCreateAPIView.as_view(),
        name="menu-item-create",
    ),
    path(
        "menu-items/<int:pk>/update/",
        MenuItemUpdateAPIView.as_view(),
        name="menu-item-update",
    ),
    path(
        "menu-items/<int:pk>/delete/",
        MenuItemDeleteAPIView.as_view(),
        name="menu-item-delete",
    ),

    # ==========================
    # Orders
    # ==========================
    path(
        "orders/",
        OrderCreateAPIView.as_view(),
        name="order-create",
    ),
    path(
        "orders/list/",
        OrderListAPIView.as_view(),
        name="order-list",
    ),
    path(
        "orders/<int:pk>/",
        OrderDetailAPIView.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<int:pk>/status/",
        OrderStatusUpdateAPIView.as_view(),
        name="order-status-update",
    ),
]