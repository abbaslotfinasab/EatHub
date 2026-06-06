// core/application/use-cases/order/DeleteOrder.ts
import type { OrderRepository } from '../../../repositories/product/OrderRepository';

export class DeleteOrder {
    constructor(private orderRepo: OrderRepository) {}

    async execute(orderId: string) {
        if (!orderId) throw new Error('شناسه سفارش معتبر نیست');
        await this.orderRepo.delete(orderId); // بک‌اند بررسی می‌کند که فقط وضعیت PENDING یا CANCELLED قابل حذف باشند
    }
}