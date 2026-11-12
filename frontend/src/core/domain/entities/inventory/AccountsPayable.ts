export type AccountsPayableStatus = 'open' | 'partially_paid' | 'paid' | 'cancelled';

export interface AccountsPayable {
    id: string;
    businessId: string;
    supplierId: string;
    supplierName: string | null;
    sourceInvoiceId: string;
    invoiceNumber: string | null;
    amount: string;
    allocatedAmount: string;
    outstandingAmount: string;
    dueDate: string | null;
    status: AccountsPayableStatus;
    postedAt: string | null;
    cancelledAt: string | null;
    cancellationReason: string;
    createdAt: string | null;
    updatedAt: string | null;
}

export interface AccountsPayableFilters {
    status?: AccountsPayableStatus;
    supplierId?: string;
    dueDateFrom?: string;
    dueDateTo?: string;
}
