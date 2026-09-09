from django.urls import path

from purchase.presentation.api.views.supplier import (
    SupplierDetailAPIView,
    SupplierListCreateAPIView,
)
from purchase.presentation.api.views.requisition import (
    RequisitionApproveAPIView,
    RequisitionDetailAPIView,
    RequisitionListCreateAPIView,
    RequisitionRejectAPIView,
    RequisitionSubmitAPIView,
)
from purchase.presentation.api.views.purchase_order import (
    PurchaseOrderCancelAPIView,
    PurchaseOrderDetailAPIView,
    PurchaseOrderListCreateAPIView,
    PurchaseOrderSendAPIView,
)
from purchase.presentation.api.views.goods_receipt import (
    GoodsReceiptDetailAPIView,
    GoodsReceiptListCreateAPIView,
)

app_name = "purchase"

urlpatterns = [
    path(
        "goods-receipts/",
        GoodsReceiptListCreateAPIView.as_view(),
        name="goods-receipt-list-create",
    ),
    path(
        "goods-receipts/<int:pk>/",
        GoodsReceiptDetailAPIView.as_view(),
        name="goods-receipt-detail",
    ),
    path(
        "purchase-orders/",
        PurchaseOrderListCreateAPIView.as_view(),
        name="purchase-order-list-create",
    ),
    path(
        "purchase-orders/<int:pk>/",
        PurchaseOrderDetailAPIView.as_view(),
        name="purchase-order-detail",
    ),
    path(
        "purchase-orders/<int:pk>/send/",
        PurchaseOrderSendAPIView.as_view(),
        name="purchase-order-send",
    ),
    path(
        "purchase-orders/<int:pk>/cancel/",
        PurchaseOrderCancelAPIView.as_view(),
        name="purchase-order-cancel",
    ),
    path(
        "requisitions/",
        RequisitionListCreateAPIView.as_view(),
        name="requisition-list-create",
    ),
    path(
        "requisitions/<int:pk>/",
        RequisitionDetailAPIView.as_view(),
        name="requisition-detail",
    ),
    path(
        "requisitions/<int:pk>/submit/",
        RequisitionSubmitAPIView.as_view(),
        name="requisition-submit",
    ),
    path(
        "requisitions/<int:pk>/approve/",
        RequisitionApproveAPIView.as_view(),
        name="requisition-approve",
    ),
    path(
        "requisitions/<int:pk>/reject/",
        RequisitionRejectAPIView.as_view(),
        name="requisition-reject",
    ),
    path(
        "suppliers/",
        SupplierListCreateAPIView.as_view(),
        name="supplier-list-create",
    ),
    path(
        "suppliers/<int:pk>/",
        SupplierDetailAPIView.as_view(),
        name="supplier-detail",
    ),
]
