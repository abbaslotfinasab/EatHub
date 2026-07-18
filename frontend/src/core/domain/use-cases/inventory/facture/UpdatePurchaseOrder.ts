


// core/application/use-cases/purchaseOrder/UpdatePurchaseOrder.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';
import type {PurchaseOrderWithItems} from "../../../entities/inventory/facture/PurchaseOrderWithItems.ts";

export class UpdatePurchaseOrder {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(input: PurchaseOrderWithItems): Promise<void> {
        if (!input.purchaseOrder.id) throw new Error('شناسه فاکتور معتبر نیست');

        // ارسال درخواست ترکیبی به ریپازیتوری (بک‌اند)
        await this.purchaseOrderRepository.update(input);
    }
}