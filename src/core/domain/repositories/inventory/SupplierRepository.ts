// core/domain/repositories/SupplierRepository.ts
import type {Supplier} from '../../entities/inventory/Supplier';
import type {SupplierFilters} from "../../objects/filters/SupplierFilters.ts";


export interface SupplierRepository {
    create(supplier: Omit<Supplier, 'id' | 'createdAt' | 'updatedAt |'>): Promise<Supplier>;
    findById(id: string): Promise<Supplier | null>;
    findAll(filters?: SupplierFilters): Promise<Supplier[]>;
    update(id: string, data: Partial<Supplier>): Promise<Supplier>;
    delete(id: string): Promise<void>;
}