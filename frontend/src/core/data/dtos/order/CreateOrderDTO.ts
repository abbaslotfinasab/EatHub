import type { CreateOrderItemDTO } from "./CreateOrderItemDTO";

export interface CreateOrderDTO {
    customer_id?: number;

    table?: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    notes?: string | null;

    items: CreateOrderItemDTO[];
}