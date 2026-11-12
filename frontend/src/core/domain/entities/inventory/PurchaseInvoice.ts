export type PurchaseInvoiceStatus = 'draft' | 'approved' | 'posted' | 'cancelled';
export type PurchaseInvoiceMatchStatus = 'not_matched' | 'pending_receipt' | 'matched' | 'exception';

export interface PurchaseInvoiceItem {
    id: string;
    ingredientId: string;
    purchaseOrderItemId: string;
    description: string;
    quantity: string;
    unitPrice: string;
    discountPercent: string;
    discountAmount: string;
    taxPercent: string;
    taxAmount: string;
    subtotal: string;
    totalPrice: string;
}

export interface PurchaseInvoice {
    id: string;
    businessId: string;
    supplierId: string;
    purchaseOrderId: string;
    invoiceNumber: string;
    invoiceDate: string;
    status: PurchaseInvoiceStatus;
    approvedAt: string | null;
    approvedById: string | null;
    postedAt: string | null;
    postedById: string | null;
    cancelledAt: string | null;
    cancelledById: string | null;
    cancellationReason: string | null;
    matchingStatus: PurchaseInvoiceMatchStatus;
    matchedAt: string | null;
    subtotal: string;
    discountPercent: string;
    discountAmount: string;
    taxPercent: string;
    taxAmount: string;
    totalPrice: string;
    createdAt: string | null;
    updatedAt: string | null;
    items: PurchaseInvoiceItem[];
}

export interface PurchaseInvoiceItemInput {
    ingredientId: string;
    purchaseOrderItemId: string;
    description: string;
    quantity: string;
    unitPrice: string;
    discountPercent: string;
    taxPercent: string;
}

export interface PurchaseInvoiceInput {
    supplierId: string;
    purchaseOrderId: string;
    invoiceNumber: string;
    invoiceDate: string;
    discountPercent: string;
    taxPercent: string;
    items: PurchaseInvoiceItemInput[];
}

export interface PurchaseInvoiceMatchLine {
    invoiceItemId: string;
    purchaseOrderItemId: string;
    orderedQuantity: string;
    acceptedReceivedQuantity: string;
    previouslyInvoicedQuantity: string;
    currentInvoiceQuantity: string;
    availableQuantity: string;
    purchaseOrderUnitPrice: string;
    invoiceUnitPrice: string;
    priceVariance: string;
    exceptions: { code: string; message: string }[];
}

export interface PurchaseInvoiceMatch {
    invoiceId: string;
    purchaseOrderId: string;
    status: PurchaseInvoiceMatchStatus;
    exceptions: { code: string; message: string }[];
    lines: PurchaseInvoiceMatchLine[];
}

export interface PurchaseInvoiceMatchResponse {
    current: PurchaseInvoiceMatch;
    lastPersisted: { status: PurchaseInvoiceMatchStatus; matchedAt: string | null };
}


export type PurchaseInvoiceEventType =
    | 'created'
    | 'updated'
    | 'approved'
    | 'match_persisted'
    | 'posted'
    | 'cancelled';

export interface PurchaseInvoiceEvent {
    id: string;
    eventType: PurchaseInvoiceEventType;
    actorId: string | null;
    actorName: string | null;
    previousStatus: string | null;
    resultingStatus: string | null;
    metadata: Record<string, unknown>;
    occurredAt: string;
}
