// core/application/use-cases/order/GetOrderByIdWithItems.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';
import type {OrderWithItems} from "../../../entities/product/order/OrderWithItems.ts";

export class GetOrderByIdWithItems {
    constructor(private orderRepo: OrderRepository) {}

    async execute(orderId: string):Promise<OrderWithItems> {
        if (!orderId) throw new Error('شناسه سفارش معتبر نیست');
        return this.orderRepo.findById(orderId);
    }
}