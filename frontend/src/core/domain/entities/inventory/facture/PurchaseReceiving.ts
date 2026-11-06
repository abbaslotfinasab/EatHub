export type ReceivingOrderStatus = 'draft' | 'sent' | 'partial' | 'received' | 'cancelled';
export type PurchaseUnit = 'kg' | 'g' | 'l' | 'ml' | 'pc';

export interface ReceivingOrderLine {
    id: string;
    ingredientId: string;
    orderedQuantity: string;
    unitPrice: string;
    purchaseUnit: PurchaseUnit | null;
}

export interface ReceivingPurchaseOrder {
    id: string;
    businessId: string;
    supplierId: string;
    requisitionId: string | null;
    status: ReceivingOrderStatus;
    orderDate: string;
    expectedDate: string | null;
    subtotal: string;
    discount: string;
    tax: string;
    total: string;
    createdAt: string;
    updatedAt: string;
    items: ReceivingOrderLine[];
}

export interface PurchaseOrderItemInput {
    ingredientId: string;
    quantity: string;
    unitPrice: string;
    purchaseUnit: PurchaseUnit;
}

export interface CreatePurchaseOrderInput {
    supplierId: string;
    requisitionId?: string;
    orderDate: string;
    expectedDate?: string | null;
    discount: string;
    tax: string;
    items: PurchaseOrderItemInput[];
}

export interface UpdatePurchaseOrderInput {
    discount: string;
    tax: string;
    items: PurchaseOrderItemInput[];
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
