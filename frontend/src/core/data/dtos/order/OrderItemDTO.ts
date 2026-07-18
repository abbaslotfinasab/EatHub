export interface OrderItemDTO {
    id: number;

    order_id: number;

    menu_item_id: number;

    menu_item_name: string;

    quantity: number;

    unit_price: number;

    total_price: number;

    notes: string | null;

    created_at: string;

    updated_at: string;
}