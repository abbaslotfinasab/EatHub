import type {
    CreateSupplierPaymentInput,
    SupplierPaymentFilters,
} from '../../../entities/inventory/SupplierPayment.ts';
import type { SupplierPaymentRepository } from '../../../repositories/inventory/SupplierPaymentRepository.ts';

const validId = (value: string) => /^\d+$/.test(value) && Number(value) > 0;

export class ListSupplierPayments {
    constructor(private readonly repository: SupplierPaymentRepository) {}

    execute(filters?: SupplierPaymentFilters) {
        if (filters?.supplierId && !validId(filters.supplierId)) {
            throw new Error('شناسه تأمین‌کننده معتبر نیست.');
        }
        if (filters?.paymentDateFrom && filters?.paymentDateTo && filters.paymentDateFrom > filters.paymentDateTo) {
            throw new Error('بازه تاریخ پرداخت معتبر نیست.');
        }
        return this.repository.list(filters);
    }
}

export class CreateSupplierPayment {
    constructor(private readonly repository: SupplierPaymentRepository) {}

    execute(input: CreateSupplierPaymentInput, idempotencyKey: string) {
        if (!validId(input.supplierId)) throw new Error('تأمین‌کننده معتبر انتخاب نشده است.');
        const amount = input.amount.trim();
        const amountMatch = /^(0|[1-9]\d*)(?:\.(\d{1,2}))?$/.exec(amount);
        if (!amountMatch) throw new Error('مبلغ پرداخت باید عددی مثبت با حداکثر دو رقم اعشار باشد.');
        const minorAmount = BigInt(amountMatch[1]) * 100n + BigInt((amountMatch[2] ?? '').padEnd(2, '0'));
        if (minorAmount <= 0n) throw new Error('مبلغ پرداخت باید عددی مثبت با حداکثر دو رقم اعشار باشد.');
        const normalizedAmount = "\${amountMatch[1]}.\${(amountMatch[2] ?? '').padEnd(2, '0')}";
        if (!/^\d{4}-\d{2}-\d{2}$/.test(input.paymentDate)) {
            throw new Error('تاریخ پرداخت معتبر نیست.');
        }
        if (!idempotencyKey) throw new Error('شناسه امن درخواست پرداخت الزامی است.');
        return this.repository.create({ ...input, amount: normalizedAmount }, idempotencyKey);
    }
}
