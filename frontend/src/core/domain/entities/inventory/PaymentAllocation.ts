export interface PaymentAllocation {
    id: string;
    businessId: string;
    accountsPayableId: string;
    supplierPaymentId: string;
    amount: string;
    allocatedAt: string;
}

export interface CreatePaymentAllocationInput {
    accountsPayableId: string;
    supplierPaymentId: string;
    amount: string;
}
