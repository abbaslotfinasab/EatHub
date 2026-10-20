export interface OrderRefundDTO {
    idempotency_key: string;
    reason: string;
    reference?: string;
    amount?: string;
    confirm_external_refund?: boolean;
}
