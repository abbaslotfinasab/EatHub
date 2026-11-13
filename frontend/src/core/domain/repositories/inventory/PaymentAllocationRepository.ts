import type { CreatePaymentAllocationInput, PaymentAllocation } from '../../entities/inventory/PaymentAllocation.ts';

export interface PaymentAllocationRepository {
    listByPayment(paymentId: string): Promise<PaymentAllocation[]>;
    create(input: CreatePaymentAllocationInput, idempotencyKey: string): Promise<PaymentAllocation>;
}
