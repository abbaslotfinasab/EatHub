// core/application/use-cases/supplier/GetSupplierById.ts
import type { SupplierRepository } from '../../../repositories/inventory/SupplierRepository';
import type { Supplier } from '../../../entities/inventory/Supplier';

export class GetSupplierById {
    constructor(private readonly supplierRepository: SupplierRepository) {}

    async execute(id: string): Promise<Supplier | null> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه تأمین‌کننده معتبر نیست');
        }

        return this.supplierRepository.findById(id);
    }
}