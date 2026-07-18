export interface UpdateOrderItemDTO {
    id?: string;

    menu_item_id: number;

    quantity: number;

    notes?: string | null;
}