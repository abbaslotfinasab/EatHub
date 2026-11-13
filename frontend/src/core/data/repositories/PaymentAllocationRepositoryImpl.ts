import type { CreatePaymentAllocationInput, PaymentAllocation } from '../../domain/entities/inventory/PaymentAllocation.ts';
import type { PaymentAllocationRepository } from '../../domain/repositories/inventory/PaymentAllocationRepository.ts';
import type { CreatePaymentAllocationDTO, PaymentAllocationDTO } from '../dtos/purchase/PaymentAllocationDTO.ts';
import { PaymentAllocationRemoteDataSource } from '../datasources/PaymentAllocationRemoteDataSource.ts';

const mapAllocation = (dto: PaymentAllocationDTO): PaymentAllocation => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    accountsPayableId: String(dto.accounts_payable_id),
    supplierPaymentId: String(dto.supplier_payment_id),
    amount: dto.amount,
    allocatedAt: dto.allocated_at,
});

export class PaymentAllocationRepositoryImpl implements PaymentAllocationRepository {
    constructor(private readonly remote = new PaymentAllocationRemoteDataSource()) {}

    async listByPayment(paymentId: string): Promise<PaymentAllocation[]> {
        return (await this.remote.listByPayment(paymentId)).map(mapAllocation);
    }

    async create(input: CreatePaymentAllocationInput, idempotencyKey: string): Promise<PaymentAllocation> {
        const payload: CreatePaymentAllocationDTO = {
            accounts_payable_id: Number(input.accountsPayableId),
            supplier_payment_id: Number(input.supplierPaymentId),
            amount: input.amount,
            idempotency_key: idempotencyKey,
        };
        return mapAllocation(await this.remote.create(payload));
    }
}
