// core/application/use-cases/supplier/UpdateSupplier.ts
import { z } from 'zod';
import { PaymentTerms } from '../../../entities/inventory/Supplier';
import type { SupplierRepository } from '../../../repositories/inventory/SupplierRepository';


const UpdateSupplierSchema = z.object({
    name: z.string().min(2, 'نام تأمین‌کننده حداقل ۲ کاراکتر است').trim().optional(),
    contactPerson: z.string().nullable().optional(),
    phone: z.string().min(5, 'شماره تلفن معتبر نیست').optional(),
    email: z.string().email('ایمیل نامعتبر').nullable().optional(),
    address: z.string().nullable().optional(),
    taxNumber: z.string().nullable().optional(),
    paymentTerms: z.nativeEnum(PaymentTerms, { message: 'شرایط پرداخت معتبر نیست' }).optional(),
    notes: z.string().nullable().optional(),
    isActive: z.boolean().optional(),
});

export type UpdateSupplierInput = z.infer<typeof UpdateSupplierSchema>;

export class UpdateSupplier {
    constructor(private readonly supplierRepository: SupplierRepository) {}

    async execute(id: string, input: UpdateSupplierInput): Promise<void> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه تأمین‌کننده معتبر نیست');
        }

        // اعتبارسنجی ورودی
        const validated = UpdateSupplierSchema.parse(input);

        // // تبدیل undefined به null برای فیلدهای nullable
        // const dataForRepo: Record<string, unknown> = {};
        // if (validated.name !== undefined) dataForRepo.name = validated.name;
        // if (validated.contactPerson !== undefined) dataForRepo.contactPerson = validated.contactPerson ?? null;
        // if (validated.phone !== undefined) dataForRepo.phone = validated.phone;
        // if (validated.email !== undefined) dataForRepo.email = validated.email ?? null;
        // if (validated.address !== undefined) dataForRepo.address = validated.address ?? null;
        // if (validated.taxNumber !== undefined) dataForRepo.taxNumber = validated.taxNumber ?? null;
        // if (validated.paymentTerms !== undefined) dataForRepo.paymentTerms = validated.paymentTerms;
        // if (validated.notes !== undefined) dataForRepo.notes = validated.notes ?? null;
        // if (validated.isActive !== undefined) dataForRepo.isActive = validated.isActive;

        // بررسی وجود تأمین‌کننده (اختیاری برای خطای زودتر)
        const existing = await this.supplierRepository.findById(id);
        if (!existing) throw new Error('تأمین‌کننده یافت نشد');

        // ارسال درخواست به ریپازیتوری (بک‌اند)
        await this.supplierRepository.update(id, validated);
    }
}