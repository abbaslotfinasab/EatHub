import type {
    CreateSupplierPaymentInput,
    SupplierPayment,
    SupplierPaymentFilters,
} from '../../domain/entities/inventory/SupplierPayment.ts';
import type { SupplierPaymentRepository } from '../../domain/repositories/inventory/SupplierPaymentRepository.ts';
import type { SupplierPaymentDTO } from '../dtos/purchase/SupplierPaymentDTO.ts';
import { SupplierPaymentRemoteDataSource } from '../datasources/SupplierPaymentRemoteDataSource.ts';

const mapPayment = (dto: SupplierPaymentDTO): SupplierPayment => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    supplierId: String(dto.supplier_id),
    amount: dto.amount,
    allocatedAmount: dto.allocated_amount,
    remainingAmount: dto.remaining_amount,
    paymentDate: dto.payment_date,
    method: dto.method,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
});

export class SupplierPaymentRepositoryImpl implements SupplierPaymentRepository {
    constructor(private readonly remote = new SupplierPaymentRemoteDataSource()) {}

    async list(filters?: SupplierPaymentFilters): Promise<SupplierPayment[]> {
        return (await this.remote.list(filters)).map(mapPayment);
    }

    async create(input: CreateSupplierPaymentInput, idempotencyKey: string): Promise<SupplierPayment> {
        return mapPayment(await this.remote.create({
            supplier_id: Number(input.supplierId),
            amount: input.amount,
            payment_date: input.paymentDate,
            method: input.method,
        }, idempotencyKey));
    }
}
