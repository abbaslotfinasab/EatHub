import type {
    PurchaseInvoiceInput,
} from '../../../entities/inventory/PurchaseInvoice.ts';
import type {
    PurchaseInvoiceFilters,
    PurchaseInvoiceRepository,
} from '../../../repositories/inventory/PurchaseInvoiceRepository.ts';

const validId = (id: string) => /^\d+$/.test(id) && Number(id) > 0;

const validateInput = (input: PurchaseInvoiceInput) => {
    if (!input.supplierId || !validId(input.supplierId)) throw new Error('تأمین‌کننده معتبر انتخاب نشده است.');
    if (!input.purchaseOrderId || !validId(input.purchaseOrderId)) throw new Error('سفارش خرید معتبر انتخاب نشده است.');
    if (!input.invoiceNumber.trim()) throw new Error('شماره فاکتور الزامی است.');
    if (!input.invoiceDate) throw new Error('تاریخ فاکتور الزامی است.');
    if (!input.items.length) throw new Error('فاکتور باید حداقل یک قلم داشته باشد.');
    const seen = new Set<string>();
    for (const item of input.items) {
        if (!validId(item.ingredientId) || !validId(item.purchaseOrderItemId)) throw new Error('قلم سفارش انتخاب‌شده معتبر نیست.');
        if (seen.has(item.purchaseOrderItemId)) throw new Error('هر قلم سفارش فقط یک‌بار می‌تواند در فاکتور باشد.');
        seen.add(item.purchaseOrderItemId);
        if (!Number.isFinite(Number(item.quantity)) || Number(item.quantity) <= 0) throw new Error('مقدار هر قلم باید بیشتر از صفر باشد.');
        if (!Number.isFinite(Number(item.unitPrice)) || Number(item.unitPrice) < 0) throw new Error('قیمت واحد معتبر نیست.');
    }
    for (const value of [input.discountPercent, input.taxPercent, ...input.items.flatMap(item => [item.discountPercent, item.taxPercent])]) {
        if (value !== '' && (!Number.isFinite(Number(value)) || Number(value) < 0)) throw new Error('درصد تخفیف و مالیات نمی‌تواند منفی باشد.');
    }
    if (Number(input.discountPercent) > 100 || input.items.some(item => Number(item.discountPercent) > 100)) {
        throw new Error('درصد تخفیف نمی‌تواند بیشتر از ۱۰۰ باشد.');
    }
};

export class ListPurchaseInvoices {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(filters?: PurchaseInvoiceFilters) { return this.repository.list(filters); }
}

export class GetPurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        return this.repository.get(id);
    }
}

export class CreatePurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(input: PurchaseInvoiceInput) {
        validateInput(input);
        return this.repository.create(input);
    }
}

export class UpdatePurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string, input: PurchaseInvoiceInput) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        validateInput(input);
        return this.repository.update(id, input);
    }
}

export class ApprovePurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        return this.repository.approve(id);
    }
}

export class MatchPurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string, persist = false) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        return this.repository.match(id, persist);
    }
}

export class PostPurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string, dueDate?: string) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        return this.repository.post(id, dueDate);
    }
}

export class CancelPurchaseInvoice {
    constructor(private readonly repository: PurchaseInvoiceRepository) {}
    execute(id: string, reason: string) {
        if (!validId(id)) throw new Error('شناسه فاکتور معتبر نیست.');
        if (!reason.trim()) throw new Error('دلیل لغو الزامی است.');
        return this.repository.cancel(id, reason);
    }
}
