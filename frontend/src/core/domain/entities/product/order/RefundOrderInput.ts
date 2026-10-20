export interface RefundOrderInput {
    orderId: string;
    idempotencyKey: string;
    reason: string;
    reference?: string;
    amount?: number;
    confirmExternalRefund?: boolean;
}

export interface RefundOrderResult {
    id: number;
    order_id: number;
    payment_method: string;
    amount: string;
    reason: string;
    reference: string;
    created_at: string;
    idempotency_key: string;
    status: "refunded";
}
