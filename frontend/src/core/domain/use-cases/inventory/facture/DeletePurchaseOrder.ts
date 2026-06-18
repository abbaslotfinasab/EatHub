// core/application/use-cases/purchaseOrder/DeletePurchaseOrder.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';

export class DeletePurchaseOrder {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(orderId: string): Promise<void> {
        if (!orderId || orderId.trim() === '') {
            throw new Error('شناسه فاکتور معتبر نیست');
        }

        // (اختیاری) بررسی وجود فاکتور برای خطای سریع‌تر
        const existing = await this.purchaseOrderRepository.findById(orderId);
        if (!existing) {
            throw new Error('فاکتور یافت نشد');
        }

        // ارسال درخواست حذف به بک‌اند (بررسی وضعیت و وابستگی‌ها در آنجا انجام می‌شود)
        await this.purchaseOrderRepository.delete(orderId);
    }
}