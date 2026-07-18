export interface UpdateOrderItemDTO {
    id?: number;

    menu_item_id: number;

    quantity: number;

    notes?: string | null;
}