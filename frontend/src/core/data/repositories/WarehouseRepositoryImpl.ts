import { apiClient } from '../http/http-client';
import type { Warehouse, WarehouseInput, WarehousePage } from '../../domain/entities/inventory/Warehouse.ts';
import type { WarehouseFilters, WarehouseRepository } from '../../domain/repositories/inventory/WarehouseRepository.ts';

interface ApiWarehouse {
    id: number;
    name: string;
    code: string | null;
    is_active: boolean;
    is_default: boolean;
    created_at: string;
    updated_at: string;
}

interface ApiPage { count: number; page: number; page_size: number; results: ApiWarehouse[] }

const fromApi = (item: ApiWarehouse): Warehouse => ({
    id: String(item.id), name: item.name, code: item.code,
    isActive: item.is_active, isDefault: item.is_default,
    createdAt: item.created_at, updatedAt: item.updated_at,
});

const toApi = (input: Partial<WarehouseInput>) => ({
    ...(input.name !== undefined ? { name: input.name } : {}),
    ...(input.code !== undefined ? { code: input.code?.trim() || null } : {}),
    ...(input.isActive !== undefined ? { is_active: input.isActive } : {}),
    ...(input.isDefault !== undefined ? { is_default: input.isDefault } : {}),
});

export class WarehouseRepositoryImpl implements WarehouseRepository {
    async list(filters: WarehouseFilters = {}): Promise<WarehousePage> {
        const { data } = await apiClient.get<ApiPage>('/inventory/warehouses/', {
            params: {
                page: filters.page ?? 1,
                page_size: filters.pageSize ?? 20,
                ...(filters.search ? { search: filters.search } : {}),
                ...(filters.isActive !== undefined ? { is_active: filters.isActive } : {}),
                ...(filters.isDefault !== undefined ? { is_default: filters.isDefault } : {}),
            },
        });
        return { count: data.count, page: data.page, pageSize: data.page_size, results: data.results.map(fromApi) };
    }

    async create(input: WarehouseInput): Promise<Warehouse> {
        const { data } = await apiClient.post<ApiWarehouse>('/inventory/warehouses/', toApi(input));
        return fromApi(data);
    }

    async update(id: string, input: Partial<WarehouseInput>): Promise<Warehouse> {
        const { data } = await apiClient.patch<ApiWarehouse>(`/inventory/warehouses/${id}/`, toApi(input));
        return fromApi(data);
    }
}
