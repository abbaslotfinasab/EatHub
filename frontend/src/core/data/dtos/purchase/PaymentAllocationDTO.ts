export interface PaymentAllocationDTO {
    id: number;
    business_id: number;
    accounts_payable_id: number;
    supplier_payment_id: number;
    amount: string;
    allocated_at: string;
    created_at: string | null;
    updated_at: string | null;
}

export interface CreatePaymentAllocationDTO {
    accounts_payable_id: number;
    supplier_payment_id: number;
    amount: string;
    idempotency_key: string;
}
