// core/application/use-cases/purchaseOrder/CreatePurchaseOrderWithItems.ts
import { z } from 'zod';
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';


// شِمای هر آیتم از فاکتور
const PurchaseOrderItemSchema = z.object({
    ingredientId: z.string().min(1, 'شناسه ماده اولیه الزامی است'),
    quantity: z.number().positive('مقدار باید مثبت باشد'),
    unitPrice: z.number().positive('قیمت واحد باید مثبت باشد'),
});

// شِمای اصلی
const CreatePurchaseOrderWithItemsSchema = z.object({
    supplierId: z.string().min(1, 'شناسه تأمین‌کننده الزامی است'),
    expectedDeliveryDate: z.string().nullable().optional(),
    invoiceNumber: z.string().nullable().optional(),
    notes: z.string().nullable().optional(),
    items: z.array(PurchaseOrderItemSchema).min(1, 'حداقل یک آیتم باید وجود داشته باشد'),
});

export type CreatePurchaseOrderWithItemsInput = z.infer<typeof CreatePurchaseOrderWithItemsSchema>;


export class CreatePurchaseOrderWithItems {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(input: CreatePurchaseOrderWithItemsInput): Promise<void> {
        // اعتبارسنجی ورودی
        const validated = CreatePurchaseOrderWithItemsSchema.parse(input);

        // (اختیاری) بررسی وجود تأمین‌کننده – می‌توان در بک‌اند انجام شود
        // اگر بخواهید در فرانت هم بررسی کنید، باید SupplierRepository تزریق شود.

        // ارسال به ریپازیتوری (بک‌اند همه چیز را در یک تراکنش انجام می‌دهد)
        await this.purchaseOrderRepository.createWithItems(validated);
    }
}