import type {
    PurchaseInvoice,
    PurchaseInvoiceInput,
    PurchaseInvoiceMatchResponse,
    PurchaseInvoiceEvent,
} from '../../entities/inventory/PurchaseInvoice.ts';

export interface PurchaseInvoiceFilters {
    supplierId?: string;
    purchaseOrderId?: string;
    dateFrom?: string;
    dateTo?: string;
}

export interface PurchaseInvoiceRepository {
    list(filters?: PurchaseInvoiceFilters): Promise<PurchaseInvoice[]>;
    get(id: string): Promise<PurchaseInvoice>;
    create(input: PurchaseInvoiceInput): Promise<PurchaseInvoice>;
    update(id: string, input: PurchaseInvoiceInput): Promise<PurchaseInvoice>;
    approve(id: string): Promise<PurchaseInvoice>;
    match(id: string, persist: boolean): Promise<PurchaseInvoiceMatchResponse>;
    post(id: string, dueDate?: string): Promise<PurchaseInvoice>;
    cancel(id: string, reason: string): Promise<PurchaseInvoice>;
    events(id: string): Promise<PurchaseInvoiceEvent[]>;
}
