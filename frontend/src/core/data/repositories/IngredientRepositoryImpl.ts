import type { Ingredient, IngredientInput, IngredientPage } from '../../domain/entities/inventory/Ingredient.ts';
import type { IngredientFilters, IngredientRepository } from '../../domain/repositories/inventory/IngredientRepository.ts';
import { apiClient } from '../http/http-client';
import { isAxiosError } from 'axios';

interface ApiIngredient {
    id: number;
    name: string;
    sku: string | null;
    unit: Ingredient['unit'];
    preparation_level: Ingredient['preparationLevel'];
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

interface ApiPage<T> {
    count: number;
    page: number;
    page_size: number;
    results: T[];
}

const fromApi = (item: ApiIngredient): Ingredient => ({
    id: String(item.id),
    name: item.name,
    sku: item.sku,
    unit: item.unit,
    preparationLevel: item.preparation_level,
    isActive: item.is_active,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
});

const toApi = (item: Partial<IngredientInput>) => ({
    ...(item.name !== undefined ? { name: item.name } : {}),
    ...(item.sku !== undefined ? { sku: item.sku?.trim() || null } : {}),
    ...(item.unit !== undefined ? { unit: item.unit } : {}),
    ...(item.preparationLevel !== undefined ? { preparation_level: item.preparationLevel } : {}),
    ...(item.isActive !== undefined ? { is_active: item.isActive } : {}),
});

export class IngredientRepositoryImpl implements IngredientRepository {
    async create(ingredient: IngredientInput): Promise<Ingredient> {
        const response = await apiClient.post<ApiIngredient>('/inventory/items/', toApi(ingredient));
        return fromApi(response.data);
    }

    async findByIds(ids: string[]): Promise<Ingredient[]> {
        return (await Promise.all(ids.map((id) => this.findById(id))))
            .filter((item): item is Ingredient => item !== null);
    }

    async findAll(filters: IngredientFilters = {}): Promise<IngredientPage> {
        const response = await apiClient.get<ApiPage<ApiIngredient>>('/inventory/items/', {
            params: {
                page: filters.page ?? 1,
                page_size: filters.pageSize ?? 20,
                ...(filters.search ? { search: filters.search } : {}),
                ...(filters.isActive !== undefined ? { is_active: filters.isActive } : {}),
                ...(filters.unit ? { unit: filters.unit } : {}),
                ...(filters.preparationLevel ? { preparation_level: filters.preparationLevel } : {}),
            },
        });
        return {
            count: response.data.count,
            page: response.data.page,
            pageSize: response.data.page_size,
            results: response.data.results.map(fromApi),
        };
    }

    async update(id: string, data: Partial<IngredientInput>): Promise<Ingredient> {
        const response = await apiClient.patch<ApiIngredient>(`/inventory/items/${id}/`, toApi(data));
        return fromApi(response.data);
    }

    async delete(id: string): Promise<void> {
        // The API has no delete operation. Keep the legacy repository method
        // safe by mapping it to the supported deactivation operation.
        await apiClient.patch(`/inventory/items/${id}/`, { is_active: false });
    }

    async findById(id: string): Promise<Ingredient | null> {
        try {
            const response = await apiClient.get<ApiIngredient>(`/inventory/items/${id}/`);
            return fromApi(response.data);
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) return null;
            throw error;
        }
    }
}
