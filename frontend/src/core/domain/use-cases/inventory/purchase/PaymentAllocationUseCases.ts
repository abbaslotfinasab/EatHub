import type { CreatePaymentAllocationInput } from '../../../entities/inventory/PaymentAllocation.ts';
import type { PaymentAllocationRepository } from '../../../repositories/inventory/PaymentAllocationRepository.ts';

const validId = (value: string) => /^\d+$/.test(value) && Number(value) > 0;

export class ListPaymentAllocations {
    constructor(private readonly repository: PaymentAllocationRepository) {}

    execute(paymentId: string) {
        if (!validId(paymentId)) throw new Error('شناسه پرداخت معتبر نیست.');
        return this.repository.listByPayment(paymentId);
    }
}

export class CreatePaymentAllocation {
    constructor(private readonly repository: PaymentAllocationRepository) {}

    execute(input: CreatePaymentAllocationInput, idempotencyKey: string) {
        if (!validId(input.accountsPayableId) || !validId(input.supplierPaymentId)) {
            throw new Error('فاکتور یا پرداخت انتخاب‌شده معتبر نیست.');
        }
        const match = /^(0|[1-9]\d*)(?:\.(\d{1,2}))?$/.exec(input.amount.trim());
        if (!match) throw new Error('مبلغ تخصیص باید عددی مثبت با حداکثر دو رقم اعشار باشد.');
        const minor = BigInt(match[1]) * 100n + BigInt((match[2] ?? '').padEnd(2, '0'));
        if (minor <= 0n) throw new Error('مبلغ تخصیص باید بیشتر از صفر باشد.');
        if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(idempotencyKey)) {
            throw new Error('شناسه امن تخصیص معتبر نیست.');
        }
        const amount = match[1] + '.' + (match[2] ?? '').padEnd(2, '0');
        return this.repository.create({ ...input, amount }, idempotencyKey);
    }
}
