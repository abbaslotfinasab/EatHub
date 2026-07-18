
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';
import type { PurchaseOrderFilters } from '../../../objects/filters/PurchaseOrderFilters.ts';

export class GetAllPurchaseOrders {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(filters?: PurchaseOrderFilters) {
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