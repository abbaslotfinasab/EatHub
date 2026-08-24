import type {CustomerDTO} from "../customer/CustomerDTO.ts";
import type {ActiveBusinessDTO} from "../business/ActiveBusinessDTO.ts";
import type {OrderItemDTO} from "./OrderItemDTO.ts";

export interface OrderDTO {
    id: string;

    customer: CustomerDTO | null;

    customer_balance: number | null;

    business: ActiveBusinessDTO;

    table: number | null;

    order_type: "dine_in" | "takeaway" | "delivery";

    status: string;

    subtotal: number;
    discount: number;
    tax: number;
    total_amount: number;

    payment_status: string;
    payment_method: string;

    notes: string | null;

    items: OrderItemDTO[];

    created_at: string;
    updated_at: string;
}