// core/application/use-cases/order/UpdateOrder.ts
import type {OrderRepository} from '../../../repositories/product/OrderRepository';
import type {OrderWithItems} from "../../../entities/product/order/OrderWithItems.ts";


export class UpdateOrder {
    constructor(private orderRepo: OrderRepository) {
    }

    async execute(
        id: string,
        order: OrderWithItems,
    ) {
        if (!id) throw new Error('شناسه سفارش معتبر نیست');

        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.orderRepo.update(
            id,
            order);
    }
}