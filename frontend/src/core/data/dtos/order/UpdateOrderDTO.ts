import type { UpdateOrderItemDTO } from "./UpdateOrderItemDTO";

export interface UpdateOrderDTO {
    customer_id?: number;

    table_id?: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    notes?: string | null;

    items: UpdateOrderItemDTO[];
}