// core/application/use-cases/order/GetOrderByIdWithItems.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';

export class GetOrderByIdWithItems {
    constructor(private orderRepo: OrderRepository) {}

    async execute(orderId: string) {
        if (!orderId) throw new Error('شناسه سفارش معتبر نیست');
        return this.orderRepo.findById(orderId);
    }
}