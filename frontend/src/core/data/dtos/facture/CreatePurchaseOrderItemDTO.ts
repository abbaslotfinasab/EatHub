export interface CreatePurchaseOrderItemDTO {

    ingredient_id: string;

    quantity: number;

    unit_price: number | null;

    total_price: number | null;

}