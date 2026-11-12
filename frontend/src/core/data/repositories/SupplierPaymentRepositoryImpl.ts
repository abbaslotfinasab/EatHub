import type {
    CreateSupplierPaymentInput,
    SupplierPayment,
} from '../../domain/entities/inventory/SupplierPayment.ts';
import type { SupplierPaymentRepository } from '../../domain/repositories/inventory/SupplierPaymentRepository.ts';
import type { CreateSupplierPaymentDTO, SupplierPaymentDTO } from '../dtos/purchase/SupplierPaymentDTO.ts';
import { SupplierPaymentRemoteDataSource } from '../datasources/SupplierPaymentRemoteDataSource.ts';

const mapPayment = (dto: SupplierPaymentDTO): SupplierPayment => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    supplierId: String(dto.supplier_id),
    amount: dto.amount,
    paymentDate: dto.payment_date,
    method: dto.method,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
});

const toCreateDTO = (input: CreateSupplierPaymentInput): CreateSupplierPaymentDTO => ({
    supplier_id: Number(input.supplierId),
    idempotency_key: input.idempotencyKey,
    amount: input.amount,
    payment_date: input.paymentDate,
    method: input.method,
});

export class SupplierPaymentRepositoryImpl implements SupplierPaymentRepository {
    constructor(private readonly remote = new SupplierPaymentRemoteDataSource()) {}

    async list(filters?: Parameters<SupplierPaymentRepository['list']>[0]): Promise<SupplierPayment[]> {
        return (await this.remote.list(filters)).map(mapPayment);
    }

    async create(input: CreateSupplierPaymentInput): Promise<SupplierPayment> {
        return mapPayment(await this.remote.create(toCreateDTO(input)));
    }
}
