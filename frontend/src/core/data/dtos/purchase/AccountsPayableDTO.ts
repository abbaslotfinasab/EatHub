export type AccountsPayableStatusDTO = 'open' | 'partially_paid' | 'paid' | 'cancelled';

export interface AccountsPayableDTO {
    id: number;
    business_id: number;
    supplier_id: number;
    supplier_name: string | null;
    source_invoice_id: number;
    invoice_number: string | null;
    amount: string;
    allocated_amount: string;
    outstanding_amount: string;
    due_date: string | null;
    status: AccountsPayableStatusDTO;
    posted_at: string | null;
    posted_by_id: number | null;
    cancelled_at: string | null;
    cancelled_by_id: number | null;
    cancellation_reason: string;
    created_at: string | null;
    updated_at: string | null;
}
