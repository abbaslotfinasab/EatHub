import type { PurchaseSupplier, PurchaseSupplierInput } from '../../domain/entities/inventory/PurchaseSupplier.ts';
import type { PurchaseSupplierRepository } from '../../domain/repositories/inventory/PurchaseSupplierRepository.ts';
import type { PurchaseSupplierDTO, PurchaseSupplierWriteDTO } from '../dtos/purchase/PurchaseSupplierDTO.ts';
import { PurchaseSupplierRemoteDataSource } from '../datasources/PurchaseSupplierRemoteDataSource.ts';

const mapSupplier = (dto: PurchaseSupplierDTO): PurchaseSupplier => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    name: dto.name,
    phone: dto.phone,
    email: dto.email,
    address: dto.address,
    taxNumber: dto.tax_number,
    notes: dto.notes,
    isActive: dto.is_active,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
});

const toWriteDTO = (input: PurchaseSupplierInput): PurchaseSupplierWriteDTO => ({
    name: input.name.trim(),
    phone: input.phone.trim(),
    email: input.email.trim(),
    address: input.address.trim(),
    tax_number: input.taxNumber.trim(),
    notes: input.notes.trim(),
    is_active: input.isActive,
});

export class PurchaseSupplierRepositoryImpl implements PurchaseSupplierRepository {
    constructor(private readonly remote = new PurchaseSupplierRemoteDataSource()) {}

    async list(filters?: { search?: string; isActive?: boolean }): Promise<PurchaseSupplier[]> {
        return (await this.remote.list(filters)).map(mapSupplier);
    }

    async create(input: PurchaseSupplierInput): Promise<PurchaseSupplier> {
        return mapSupplier(await this.remote.create(toWriteDTO(input)));
    }

    async update(id: string, input: PurchaseSupplierInput): Promise<PurchaseSupplier> {
        return mapSupplier(await this.remote.update(id, toWriteDTO(input)));
    }
}
