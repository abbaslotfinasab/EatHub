export type SupplierPaymentMethodDTO = 'cash' | 'bank_transfer' | 'card' | 'cheque' | 'credit' | 'other';

export interface SupplierPaymentDTO {
    id: number;
    business_id: number;
    supplier_id: number;
    amount: string;
    allocated_amount: string;
    remaining_amount: string;
    payment_date: string;
    method: SupplierPaymentMethodDTO;
    created_at: string | null;
    updated_at: string | null;
}

export interface CreateSupplierPaymentDTO {
    supplier_id: number;
    amount: string;
    payment_date: string;
    method: SupplierPaymentMethodDTO;
    idempotency_key: string;
}
