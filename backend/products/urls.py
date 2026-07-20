from django.urls import path

from products.views import *

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
        "orders/<int:order_id>/status/",
        OrderStatusUpdateAPIView.as_view(),
        name="order-status-update",
    ),

    path(
        "orders/<int:pk>/update/",
        OrderUpdateAPIView.as_view(),
        name="order-update",
    ),

    path(
        "orders/<int:pk>/delete/",
        OrderDeleteAPIView.as_view(),
        name="order-delete",
    ),

    # ==========================
    # Customers
    # ==========================
    path(
        "customers/",
        CustomerListAPIView.as_view(),
        name="customer-list",
    ),


    path(
        "customers/create",
        CustomerCreateAPIView.as_view(),
        name="customer-create",
    ),

    path(
        "customers/<int:pk>/",
        CustomerDetailAPIView.as_view(),
        name="customer-detail",
    ),

    path(
        "customers/<int:pk>/update/",
        CustomerUpdateAPIView.as_view(),
        name="customer-update",
    ),

    path(
        "customers/<int:pk>/delete/",
        CustomerDeleteAPIView.as_view(),
        name="customer-delete",
    ),

    # ==========================
    # Customer Account
    # ==========================

    path(
        "customers/<int:customer_id>/account/",
        CustomerAccountDetailAPIView.as_view(),
        name="customer-account",
    ),

    path(
        "customers/<int:customer_id>/credit/",
        CustomerCreditAPIView.as_view(),
        name="customer-credit",
    ),

    path(
        "customers/<int:customer_id>/transactions/",
        CustomerTransactionListAPIView.as_view(),
        name="customer-transactions",
    ),
    path(
        "customers/<int:customer_id>/debit/",
        CustomerDebitAPIView.as_view(),
        name="customer-debit",
    ),

    path(
        "customers/<int:customer_id>/adjust/",
        CustomerAdjustAPIView.as_view(),
        name="customer-adjust",
    ),

]
