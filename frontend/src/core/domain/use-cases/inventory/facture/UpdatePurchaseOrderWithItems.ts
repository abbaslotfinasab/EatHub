// core/application/use-cases/purchaseOrder/UpdatePurchaseOrderWithItems.ts
import { z } from 'zod';
import { PurchaseOrderStatus } from '../../../entities/inventory/PurchaseOrder';

// شِمای هر آیتم (برای جایگزینی کامل)
const PurchaseOrderItemUpdateSchema = z.object({
    ingredientId: z.string().min(1),
    quantity: z.number().positive(),
    unitPrice: z.number().positive(),
});

const UpdatePurchaseOrderWithItemsSchema = z.object({
    // فیلدهای اصلی فاکتور (همگی اختیاری)
    supplierId: z.string().min(1).optional(),
    expectedDeliveryDate: z.string().nullable().optional(),
    invoiceNumber: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    status: z.nativeEnum(PurchaseOrderStatus).optional(),
    // لیست جدید آیتم‌ها (در صورت ارسال، جایگزین آیتم‌های قبلی می‌شود)
    items: z.array(PurchaseOrderItemUpdateSchema).optional(),
});

export type UpdatePurchaseOrderWithItemsInput = z.infer<typeof UpdatePurchaseOrderWithItemsSchema>;


// core/application/use-cases/purchaseOrder/UpdatePurchaseOrderWithItems.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';

export class UpdatePurchaseOrderWithItems {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(orderId: string, input: UpdatePurchaseOrderWithItemsInput): Promise<void> {
        if (!orderId) throw new Error('شناسه فاکتور معتبر نیست');

        const validated = UpdatePurchaseOrderWithItemsSchema.parse(input);

        // ارسال درخواست ترکیبی به ریپازیتوری (بک‌اند)
        await this.purchaseOrderRepository.updateWithItems(orderId, validated);
    }
}