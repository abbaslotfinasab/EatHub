// core/domain/repositories/SupplierRepository.ts
import type {Supplier} from '../../entities/inventory/Supplier';

export interface SupplierFilters {
    isActive?: boolean;
    search?: string;   // جستجو در name, contactPerson, phone
}

export interface SupplierRepository {
    create(supplier: Omit<Supplier, 'id'>): Promise<Supplier>;
    findById(id: string): Promise<Supplier | null>;
    findAll(filters?: SupplierFilters): Promise<Supplier[]>;
    update(id: string, data: Partial<Supplier>): Promise<Supplier>;
    delete(id: string): Promise<void>;
}