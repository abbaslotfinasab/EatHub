// core/application/use-cases/order/UpdateOrderWithItems.ts
import { z } from 'zod';
import type { OrderRepository } from '../../../repositories/product/OrderRepository';
import type {OrderResult} from "../../../entities/product/OrderResult.ts";

// شِمای هر آیتم سفارش (برای جایگزینی کامل)
const UpdateOrderItemSchema = z.object({
    menuItemId: z.string(),
    quantity: z.number().positive(),
    notes: z.string().nullable().optional(),
    // در صورت نیاز می‌توان unitPrice را هم دریافت کرد، اما معمولاً قیمت از آیتم منو خوانده می‌شود.
    // برای سادگی فعلاً menuItemId و quantity کافی است.
});

// شمای اصلی ورودی
const UpdateOrderSchema = z.object({
    customerName: z.string().min(1).optional(),
    customerPhone: z.string().optional(),
    tableId: z.string().nullable().optional(),
    orderType: z.enum(['dine_in', 'takeaway', 'delivery']).optional(),
    notes: z.string().nullable().optional(),
    discount: z.number().min(0).optional(),
    items: z.array(UpdateOrderItemSchema).optional(), // اگر ارسال شود، جایگزین آیتم‌های قبلی می‌شود
});

export type UpdateOrderInput = z.infer<typeof UpdateOrderSchema>;

export class UpdateOrderWithItems {
    constructor(private orderRepo: OrderRepository) {}

    async execute(orderId: string, input: UpdateOrderInput): Promise<OrderResult> {
        if (!orderId) throw new Error('شناسه سفارش معتبر نیست');

        const validated = UpdateOrderSchema.parse(input);

        // جدا کردن items از بقیه فیلدهای Order
        const { items, ...orderData } = validated;

        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.orderRepo.update(orderId, orderData, items);
    }
}