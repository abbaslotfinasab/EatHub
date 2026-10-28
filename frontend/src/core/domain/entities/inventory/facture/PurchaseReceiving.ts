export type ReceivingOrderStatus = 'draft' | 'sent' | 'partial' | 'received' | 'cancelled';

export interface ReceivingOrderLine {
    id: string;
    ingredientId: string;
    orderedQuantity: string;
    unitPrice: string;
    purchaseUnit: string | null;
}

export interface ReceivingPurchaseOrder {
    id: string;
    businessId: string;
    supplierId: string;
    status: ReceivingOrderStatus;
    orderDate: string;
    expectedDate: string | null;
    items: ReceivingOrderLine[];
}

export interface GoodsReceiptLine {
    id: string;
    purchaseOrderItemId: string;
    receivedQuantity: string;
    rejectedQuantity: string;
    purchaseUnit: string | null;
}

export interface GoodsReceipt {
    id: string;
    purchaseOrderId: string;
    receivedDate: string;
    notes: string;
    warehouseId: string | null;
    items: GoodsReceiptLine[];
}

export interface ReceiptLineInput {
    purchaseOrderItemId: string;
    receivedQuantity: string;
    purchaseUnit: string;
}

export interface CreateGoodsReceiptInput {
    idempotencyKey: string;
    purchaseOrderId: string;
    receivedDate: string;
    notes: string;
    warehouseId: string;
    items: ReceiptLineInput[];
}

export interface PurchaseSupplierSummary {
    id: string;
    name: string;
}
