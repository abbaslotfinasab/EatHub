// core/application/use-cases/purchaseOrder/CreatePurchaseOrder.ts
import type { PurchaseOrderRepository } from '../../../repositories/inventory/PurchaseOrderRepository';
import type {PurchaseOrderWithItems} from "../../../entities/inventory/facture/PurchaseOrderWithItems.ts";



// شِمای اصلی

export class CreatePurchaseOrder {
    constructor(private readonly purchaseOrderRepository: PurchaseOrderRepository) {}

    async execute(input: PurchaseOrderWithItems): Promise<void> {

        // ارسال به ریپازیتوری (بک‌اند همه چیز را در یک تراکنش انجام می‌دهد)
        await this.purchaseOrderRepository.create(input);
    }
}