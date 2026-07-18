export interface PurchaseOrderItemDTO {
    id: string;

    purchase_order_id: string;

    component_id: string;

    quantity: number;

    unit_price: number;

    total_price: number;

    created_at: string;
    updated_at: string;
}