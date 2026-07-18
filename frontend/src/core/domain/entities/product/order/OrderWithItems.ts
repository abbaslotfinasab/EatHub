import type {Order} from "./Order.ts";
import type {OrderItem} from "./OrderItem.ts";

export interface OrderWithItems {
    order: Order;
    orderItems: OrderItem[];
}
