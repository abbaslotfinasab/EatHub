export type SupplierPaymentMethod = 'cash' | 'bank_transfer' | 'card' | 'cheque' | 'credit' | 'other';

export interface SupplierPayment {
    id: string;
    businessId: string;
    supplierId: string;
    amount: string;
    paymentDate: string;
    method: SupplierPaymentMethod;
    createdAt: string | null;
    updatedAt: string | null;
}

export interface SupplierPaymentFilters {
    supplierId?: string;
    method?: SupplierPaymentMethod;
    paymentDateFrom?: string;
    paymentDateTo?: string;
}

export interface CreateSupplierPaymentInput {
    supplierId: string;
    amount: string;
    paymentDate: string;
    method: SupplierPaymentMethod;
    idempotencyKey: string;
}
