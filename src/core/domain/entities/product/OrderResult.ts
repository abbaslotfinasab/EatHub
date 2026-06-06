import type {Order} from "./Order.ts";
import type {OrderItem} from "./OrderItem.ts";

export interface OrderResult {
    order: Order;
    orderItems: OrderItem[];
}
