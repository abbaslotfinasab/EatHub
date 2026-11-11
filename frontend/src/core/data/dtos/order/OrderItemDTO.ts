export interface OrderItemDTO {
    id: number;
    order_id: number;
    menu_item_id: number | null;
    menu_item_name: string;
    catalog_product_id?: number | null;
    catalog_product_name?: string | null;
    quantity: number;
    unit_price: number;
    total_price: number;
    notes: string | null;
    created_at?: string;
    updated_at?: string;
}
