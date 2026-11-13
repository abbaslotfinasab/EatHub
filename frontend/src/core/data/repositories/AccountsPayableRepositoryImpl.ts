import type { AccountsPayable } from '../../domain/entities/inventory/AccountsPayable.ts';
import type { AccountsPayableRepository } from '../../domain/repositories/inventory/AccountsPayableRepository.ts';
import type { AccountsPayableDTO } from '../dtos/purchase/AccountsPayableDTO.ts';
import { AccountsPayableRemoteDataSource } from '../datasources/AccountsPayableRemoteDataSource.ts';

const mapPayable = (dto: AccountsPayableDTO): AccountsPayable => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    supplierId: String(dto.supplier_id),
    supplierName: dto.supplier_name,
    sourceInvoiceId: String(dto.source_invoice_id),
    invoiceNumber: dto.invoice_number,
    amount: dto.amount,
    allocatedAmount: dto.allocated_amount,
    outstandingAmount: dto.outstanding_amount,
    dueDate: dto.due_date,
    status: dto.status,
    postedAt: dto.posted_at,
    cancelledAt: dto.cancelled_at,
    cancellationReason: dto.cancellation_reason,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
});

export class AccountsPayableRepositoryImpl implements AccountsPayableRepository {
    constructor(private readonly remote = new AccountsPayableRemoteDataSource()) {}

    async list(filters?: Parameters<AccountsPayableRepository['list']>[0]): Promise<AccountsPayable[]> {
        return (await this.remote.list(filters)).map(mapPayable);
    }
}
