// core/application/use-cases/supplier/DeleteSupplier.ts
import type { SupplierRepository } from '../../../repositories/inventory/SupplierRepository';

export class DeleteSupplier {
    constructor(private readonly supplierRepository: SupplierRepository) {}

    async execute(supplierId: string): Promise<void> {
        if (!supplierId || supplierId.trim() === '') {
            throw new Error('شناسه تأمین‌کننده معتبر نیست');
        }

        // بررسی وجود تأمین‌کننده (اختیاری، می‌تواند صرفاً جهت خطای سریع‌تر باشد)
        const existing = await this.supplierRepository.findById(supplierId);
        if (!existing) {
            throw new Error('تأمین‌کننده یافت نشد');
        }

        // ارسال درخواست حذف به بک‌اند
        await this.supplierRepository.delete(supplierId);
    }
}