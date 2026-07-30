import type { UpdateOrderItemDTO } from "./UpdateOrderItemDTO";

export interface UpdateOrderDTO {
    customer?: number;

    table?: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    notes?: string | null;

    items: UpdateOrderItemDTO[];
}