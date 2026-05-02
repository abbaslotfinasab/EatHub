// core/application/use-cases/supplier/CreateSupplier.ts
import type { SupplierRepository } from '../../../repositories/inventory/SupplierRepository';
import { z } from 'zod';
import { PaymentTerms } from '../../../entities/inventory/Supplier';

const CreateSupplierSchema = z.object({
    name: z.string().min(2, 'نام تأمین‌کننده حداقل ۲ کاراکتر است').trim(),
    contactPerson: z.string().nullable().optional(),
    phone: z.string().min(5, 'شماره تلفن معتبر نیست'),
    email: z.string().email('ایمیل نامعتبر').nullable().optional(),
    address: z.string().nullable().optional(),
    taxNumber: z.string().nullable().optional(),
    paymentTerms: z.nativeEnum(PaymentTerms, { message: 'شرایط پرداخت معتبر نیست' }),
    notes: z.string().nullable().optional(),
    isActive: z.boolean().optional().default(true),
});

export type CreateSupplierInput = z.infer<typeof CreateSupplierSchema>;
export class CreateSupplier {
    constructor(private readonly supplierRepository: SupplierRepository) {}

    async execute(input: CreateSupplierInput): Promise<void> {
        // اعتبارسنجی سطحی
        const validated = CreateSupplierSchema.parse(input);

        // ارسال به ریپازیتوری (بک‌اند بقیه کارها را انجام می‌دهد)
        await this.supplierRepository.create(validated);
    }
}