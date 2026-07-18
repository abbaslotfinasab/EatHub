import type { OrderItemDTO } from "./OrderItemDTO";

export interface OrderDTO {
    id: string;

    customer_id: number | null;

    customer_name: string;

    customer_phone: string | null;

    table: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    status: string;

    subtotal: number;

    discount: number;

    tax: number;

    total_amount: number;

    payment_status:string;

    notes: string | null;

    items: OrderItemDTO[];

    created_at: string;

    updated_at: string;
}