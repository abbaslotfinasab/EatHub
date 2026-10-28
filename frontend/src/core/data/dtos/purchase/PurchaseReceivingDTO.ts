export interface PurchaseOrderLineReadDTO {
    id: number;
    ingredient_id: number;
    quantity: string;
    unit_price: string;
    purchase_unit: string | null;
}

export interface PurchaseOrderReadDTO {
    id: number;
    business_id: number;
    supplier_id: number;
    status: 'draft' | 'sent' | 'partial' | 'received' | 'cancelled';
    order_date: string;
    expected_date: string | null;
    items: PurchaseOrderLineReadDTO[];
}

export interface GoodsReceiptLineReadDTO {
    id: number;
    purchase_order_item_id: number;
    received_quantity: string;
    rejected_quantity: string;
    purchase_unit: string | null;
}

export interface GoodsReceiptReadDTO {
    id: number;
    purchase_order_id: number;
    received_date: string;
    notes: string;
    warehouse_id: number | null;
    items: GoodsReceiptLineReadDTO[];
}

export interface CreateGoodsReceiptDTO {
    idempotency_key: string;
    purchase_order_id: number;
    received_date: string;
    notes: string;
    warehouse_id: number;
    items: {
        purchase_order_item_id: number;
        received_quantity: string;
        purchase_unit: string;
    }[];
}

export interface SupplierSummaryDTO {
    id: number;
    name: string;
}
