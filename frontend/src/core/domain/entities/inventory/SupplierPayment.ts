export type SupplierPaymentMethod = 'cash' | 'bank_transfer' | 'card' | 'cheque' | 'credit' | 'other';

export interface SupplierPayment {
    id: string;
    businessId: string;
    supplierId: string;
    amount: string;
    allocatedAmount: string;
    remainingAmount: string;
    paymentDate: string;
    method: SupplierPaymentMethod;
    createdAt: string | null;
    updatedAt: string | null;
}

export interface CreateSupplierPaymentInput {
    supplierId: string;
    amount: string;
    paymentDate: string;
    method: SupplierPaymentMethod;
}

export interface SupplierPaymentFilters {
    supplierId?: string;
    method?: SupplierPaymentMethod;
    paymentDateFrom?: string;
    paymentDateTo?: string;
}
