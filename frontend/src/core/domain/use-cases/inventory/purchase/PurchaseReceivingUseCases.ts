import type { CreateGoodsReceiptInput } from '../../../entities/inventory/facture/PurchaseReceiving.ts';
import type { PurchaseReceivingRepository } from '../../../repositories/inventory/PurchaseReceivingRepository.ts';

export class ListReceivingOrders {
    constructor(private readonly repository: PurchaseReceivingRepository) {}
    execute() { return this.repository.listOrders(); }
}

export class GetReceivingOrder {
    constructor(private readonly repository: PurchaseReceivingRepository) {}
    execute(id: string) {
        if (!/^\d+$/.test(id) || Number(id) <= 0) throw new Error('شناسه سفارش خرید معتبر نیست.');
        return this.repository.getOrder(id);
    }
}

export class ListOrderGoodsReceipts {
    constructor(private readonly repository: PurchaseReceivingRepository) {}
    execute(orderId: string) {
        if (!/^\d+$/.test(orderId) || Number(orderId) <= 0) throw new Error('شناسه سفارش خرید معتبر نیست.');
        return this.repository.listReceipts(orderId);
    }
}

export class CreateOrderGoodsReceipt {
    constructor(private readonly repository: PurchaseReceivingRepository) {}
    execute(input: CreateGoodsReceiptInput) {
        if (!input.items.length) throw new Error('برای ثبت دریافت، حداقل یک ردیف با مقدار مثبت انتخاب کنید.');
        return this.repository.createReceipt(input);
    }
}

export class ListPurchaseSuppliers {
    constructor(private readonly repository: PurchaseReceivingRepository) {}
    execute() { return this.repository.listSuppliers(); }
}
