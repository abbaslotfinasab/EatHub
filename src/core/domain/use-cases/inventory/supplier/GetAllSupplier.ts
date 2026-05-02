// core/application/use-cases/supplier/GetAllSuppliers.ts
import type { SupplierRepository, SupplierFilters } from '../../../repositories/inventory/SupplierRepository';
import type {Supplier} from "../../../entities/inventory/Supplier.ts";

export class GetAllSuppliers {
    constructor(private readonly supplierRepository: SupplierRepository) {}

    async execute(filters?: SupplierFilters): Promise<Supplier[]> {
        // (اختیاری) اعتبارسنجی ساده فیلترها
        if (filters?.search !== undefined && typeof filters.search !== 'string') {
            throw new Error('فیلتر جستجو باید رشته باشد');
        }

        // ارسال درخواست به ریپازیتوری که خود API را صدا می‌زند
        return this.supplierRepository.findAll(filters);
    }
}