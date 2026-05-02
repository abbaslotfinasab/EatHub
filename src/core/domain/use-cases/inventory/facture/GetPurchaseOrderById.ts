// core/application/use-cases/purchaseOrder/GetPurchaseOrderById.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';
import type { PurchaseOrder } from '../../../entities/inventory/PurchaseOrder';

export class GetPurchaseOrderById {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(id: string): Promise<PurchaseOrder | null> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه فاکتور معتبر نیست');
        }

        return this.purchaseOrderRepository.findById(id);
    }
}