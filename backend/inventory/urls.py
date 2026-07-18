from django.urls import path

from inventory.views import *


app_name = 'inventory'


urlpatterns = [

    path(
        "purchase-orders/create/",
        PurchaseOrderCreateAPIView.as_view(),
    ),

    path(
        "purchase-orders/",
        PurchaseOrderListAPIView.as_view(),
    ),

    path(
        "purchase-orders/<int:pk>/",
        PurchaseOrderDetailAPIView.as_view(),
    ),

    path(
        "purchase-orders/<int:pk>/update/",
        PurchaseOrderUpdateAPIView.as_view(),
    ),

    path(
        "purchase-orders/<int:pk>/delete/",
        PurchaseOrderDeleteAPIView.as_view(),
    ),

    path(
        "purchase-orders/<int:pk>/status/",
        PurchaseOrderStatusUpdateAPIView.as_view(),
    ),

]