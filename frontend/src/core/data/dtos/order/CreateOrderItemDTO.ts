export interface CreateOrderItemDTO {
    menu_item_id: number;

    quantity: number;

    notes?: string | null;
}