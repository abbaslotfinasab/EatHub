import type { CreateOrderItemDTO } from "./CreateOrderItemDTO";

export interface CreateOrderDTO {
    idempotency_key: string;
    customer_id?: number;

    table?: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    notes?: string | null;

    items: CreateOrderItemDTO[];
}