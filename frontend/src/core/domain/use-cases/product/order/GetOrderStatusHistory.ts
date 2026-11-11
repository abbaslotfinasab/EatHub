import type {OrderRepository} from "../../../repositories/product/OrderRepository.ts";
import type {OrderStatusHistory} from "../../../entities/product/order/OrderStatusHistory.ts";

export class GetOrderStatusHistory {
    constructor(private readonly orderRepository: OrderRepository) {}

    async execute(orderId: string): Promise<OrderStatusHistory> {
        if (!orderId) throw new Error("شناسه سفارش معتبر نیست");
        return this.orderRepository.getStatusHistory(orderId);
    }
}
