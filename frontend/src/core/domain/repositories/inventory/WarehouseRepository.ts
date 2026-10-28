import type { Warehouse, WarehouseInput, WarehousePage } from '../../entities/inventory/Warehouse.ts';

export interface WarehouseFilters {
    page?: number;
    pageSize?: number;
    search?: string;
    isActive?: boolean;
    isDefault?: boolean;
}

export interface WarehouseRepository {
    list(filters?: WarehouseFilters): Promise<WarehousePage>;
    create(input: WarehouseInput): Promise<Warehouse>;
    update(id: string, input: Partial<WarehouseInput>): Promise<Warehouse>;
}
