export type PurchaseOrderStatusDTO = 'draft' | 'sent' | 'partial' | 'received' | 'cancelled';
export type PurchaseUnitDTO = 'kg' | 'g' | 'l' | 'ml' | 'pc';

export interface PurchaseOrderLineReadDTO {
    id: number;
    ingredient_id: number;
    quantity: string;
    unit_price: string;
    purchase_unit: PurchaseUnitDTO | null;
}

export interface PurchaseOrderReadDTO {
    id: number;
    business_id: number;
    supplier_id: number;
    requisition_id: number | null;
    status: PurchaseOrderStatusDTO;
    order_date: string;
    expected_date: string | null;
    subtotal: string;
    discount: string;
    tax: string;
    total: string;
    items: PurchaseOrderLineReadDTO[];
    created_at: string;
    updated_at: string;
}

export interface PurchaseOrderItemWriteDTO {
    ingredient_id: number;
    quantity: string;
    unit_price: string;
    purchase_unit: PurchaseUnitDTO;
}

export interface CreatePurchaseOrderDTO {
    supplier_id: number;
    requisition_id?: number;
    order_date: string;
    expected_date?: string | null;
    discount?: string;
    tax?: string;
    items: PurchaseOrderItemWriteDTO[];
}

export interface UpdatePurchaseOrderDTO {
    discount?: string;
    tax?: string;
    items: PurchaseOrderItemWriteDTO[];
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
