export type PurchaseInvoiceStatusDTO = 'draft' | 'approved' | 'posted' | 'cancelled';
export type PurchaseInvoiceMatchStatusDTO = 'not_matched' | 'pending_receipt' | 'matched' | 'exception';

export interface PurchaseInvoiceItemDTO {
    id: number;
    ingredient_id: number;
    purchase_order_item_id: number;
    description: string;
    quantity: string;
    unit_price: string;
    discount_percent: string;
    discount_amount: string;
    tax_percent: string;
    tax_amount: string;
    subtotal: string;
    total_price: string;
}

export interface PurchaseInvoiceDTO {
    id: number;
    business_id: number;
    supplier_id: number;
    purchase_order_id: number;
    invoice_number: string;
    invoice_date: string;
    status: PurchaseInvoiceStatusDTO;
    approved_at: string | null;
    approved_by_id: number | null;
    posted_at: string | null;
    posted_by_id: number | null;
    cancelled_at: string | null;
    cancelled_by_id: number | null;
    cancellation_reason: string | null;
    matching_status: PurchaseInvoiceMatchStatusDTO;
    matched_at: string | null;
    subtotal: string;
    discount_percent: string;
    discount_amount: string;
    tax_percent: string;
    tax_amount: string;
    total_price: string;
    items: PurchaseInvoiceItemDTO[];
    created_at: string | null;
    updated_at: string | null;
}

export interface PurchaseInvoiceItemWriteDTO {
    ingredient_id: number;
    purchase_order_item_id: number;
    quantity: string;
    unit_price: string;
    description: string;
    discount_percent: string;
    tax_percent: string;
}

export interface PurchaseInvoiceWriteDTO {
    supplier_id: number;
    purchase_order_id: number;
    invoice_number: string;
    invoice_date: string;
    discount_percent: string;
    tax_percent: string;
    items: PurchaseInvoiceItemWriteDTO[];
}

export interface PurchaseInvoiceMatchLineDTO {
    invoice_item_id: number;
    purchase_order_item_id: number;
    ordered_quantity: string;
    accepted_received_quantity: string;
    previously_invoiced_quantity: string;
    current_invoice_quantity: string;
    available_quantity: string;
    purchase_order_unit_price: string;
    invoice_unit_price: string;
    price_variance: string;
    exceptions: { code: string; message: string }[];
}

export interface PurchaseInvoiceMatchResultDTO {
    invoice_id: number;
    purchase_order_id: number;
    status: PurchaseInvoiceMatchStatusDTO;
    exceptions: { code: string; message: string }[];
    lines: PurchaseInvoiceMatchLineDTO[];
}

export interface PurchaseInvoiceMatchResponseDTO {
    current: PurchaseInvoiceMatchResultDTO;
    last_persisted: { status: PurchaseInvoiceMatchStatusDTO; matched_at: string | null };
}

export interface PostPurchaseInvoiceResponseDTO {
    invoice: PurchaseInvoiceDTO;
    accounts_payable: {
        id: number;
        source_invoice_id: number;
        amount: string;
        due_date: string | null;
        status: string;
    };
}
