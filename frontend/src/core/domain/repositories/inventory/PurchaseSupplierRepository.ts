import type { PurchaseSupplier, PurchaseSupplierInput } from '../../entities/inventory/PurchaseSupplier.ts';

export interface PurchaseSupplierRepository {
    list(filters?: { search?: string; isActive?: boolean }): Promise<PurchaseSupplier[]>;
    create(input: PurchaseSupplierInput): Promise<PurchaseSupplier>;
    update(id: string, input: PurchaseSupplierInput): Promise<PurchaseSupplier>;
}
