// core/application/use-cases/purchaseOrder/GetPurchaseOrderById.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';

export class GetPurchaseOrderById {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(id: string){
        if (!id || id.trim() === '') {
            throw new Error('شناسه فاکتور معتبر نیست');
        }

        return this.purchaseOrderRepository.findById(id);
    }
}