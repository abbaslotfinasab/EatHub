import type {
    CreateSupplierPaymentInput,
    SupplierPayment,
    SupplierPaymentFilters,
} from '../../entities/inventory/SupplierPayment.ts';

export interface SupplierPaymentRepository {
    list(filters?: SupplierPaymentFilters): Promise<SupplierPayment[]>;
    create(input: CreateSupplierPaymentInput): Promise<SupplierPayment>;
}
