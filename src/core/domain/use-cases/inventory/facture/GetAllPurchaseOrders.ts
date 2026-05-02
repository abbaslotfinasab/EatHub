// core/application/use-cases/purchaseOrder/GetAllPurchaseOrders.ts
import type { PurchaseOrderFilters } from '../../../repositories/inventory/PurchaseOrderRepository';

// در صورت تمایل می‌توانید فیلترها را دوباره صادر کنید یا فقط از ریپازیتوری استفاده کنید
export type { PurchaseOrderFilters };
// core/application/use-cases/purchaseOrder/GetAllPurchaseOrders.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';
import type { PurchaseOrder } from '../../../entities/inventory/PurchaseOrder';

export class GetAllPurchaseOrders {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(filters?: PurchaseOrderFilters): Promise<PurchaseOrder[]> {
        // اعتبارسنجی ساده (اختیاری)
        if (filters?.fromDate && isNaN(Date.parse(filters.fromDate))) {
            throw new Error('فرمت تاریخ شروع نامعتبر است');
        }
        if (filters?.toDate && isNaN(Date.parse(filters.toDate))) {
            throw new Error('فرمت تاریخ پایان نامعتبر است');
        }

        return this.purchaseOrderRepository.findAll(filters);
    }
}