import type {
    CreateSupplierPaymentInput,
    SupplierPaymentFilters,
} from '../../../entities/inventory/SupplierPayment.ts';
import type { SupplierPaymentRepository } from '../../../repositories/inventory/SupplierPaymentRepository.ts';

const validId = (value: string) => /^\\d+$/.test(value) && Number(value) > 0;
const validDate = (value: string) => /^\\d{4}-\\d{2}-\\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));

export class ListSupplierPayments {
    constructor(private readonly repository: SupplierPaymentRepository) {}

    execute(filters?: SupplierPaymentFilters) {
        if (filters?.supplierId && !validId(filters.supplierId)) {
            throw new Error('شناسه تأمین‌کننده معتبر نیست.');
        }
        if (filters?.paymentDateFrom && !validDate(filters.paymentDateFrom)) {
            throw new Error('تاریخ شروع معتبر نیست.');
        }
        if (filters?.paymentDateTo && !validDate(filters.paymentDateTo)) {
            throw new Error('تاریخ پایان معتبر نیست.');
        }
        if (filters?.paymentDateFrom && filters?.paymentDateTo && filters.paymentDateFrom > filters.paymentDateTo) {
            throw new Error('بازه تاریخ پرداخت معتبر نیست.');
        }
        return this.repository.list(filters);
    }
}

export class CreateSupplierPayment {
    constructor(private readonly repository: SupplierPaymentRepository) {}

    execute(input: CreateSupplierPaymentInput) {
        if (!validId(input.supplierId)) throw new Error('تأمین‌کننده معتبر نیست.');
        if (!/^\\d+(?:\\.\\d{1,2})?$/.test(input.amount) || Number(input.amount) <= 0) {
            throw new Error('مبلغ پرداخت باید عددی مثبت با حداکثر دو رقم اعشار باشد.');
        }
        if (!validDate(input.paymentDate)) throw new Error('تاریخ پرداخت معتبر نیست.');
        if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(input.idempotencyKey)) {
            throw new Error('شناسه امن درخواست معتبر نیست.');
        }
        return this.repository.create(input);
    }
}
