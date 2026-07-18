// core/data/repositories/IngredientRepositoryImpl.ts
import type { IngredientRepository, IngredientFilters } from '../../domain/repositories/inventory/IngredientRepository';
import type { Ingredient } from '../../domain/entities/inventory/Ingredient';
import { apiClient } from '../http/http-client';
import { isAxiosError } from 'axios';
import {mockIngredients} from "../dtos/ingredient/ingredients.ts";

export class IngredientRepositoryImpl implements IngredientRepository {
    async create(ingredient: Omit<Ingredient, 'id' | 'createdAt' | 'updatedAt'>): Promise<Ingredient> {
        const response = await apiClient.post('/ingredients', ingredient);
        return response.data;
    }

    async findByIds(id: string[]): Promise<Ingredient[]> {
        try {
            const response = await apiClient.get(`/ingredients/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return [];
            }
            throw error;
        }
    }

    async findAll(filters?: IngredientFilters): Promise<Ingredient[]> {


            console.log('🔧 Using mock ingredients data');
            let data = [...mockIngredients];
            // اعمال فیلترهای ساده (اختیاری)
            if (filters?.search) {
                const term = filters.search.toLowerCase();
                data = data.filter(i => i.name.toLowerCase().includes(term));
            }
            if (filters?.lowStock) {
                data = data.filter(i => i.currentStock <= i.reorderLevel);
            }
            if (filters?.isActive !== undefined) {
                data = data.filter(i => i.isActive === filters.isActive);
            }
            return Promise.resolve(data);
        }
        // const params = new URLSearchParams();
        // if (filters) {
        //     Object.entries(filters).forEach(([key, value]) => {
        //         if (value !== undefined && value !== null) {
        //             params.append(key, String(value));
        //         }
        //     });
        // }
        // const queryString = params.toString();
        // const url = queryString ? `/ingredients?${queryString}` : '/ingredients';
        // const response = await apiClient.get(url);
        // return response.data;


    async update(id: string, data: Partial<Ingredient>): Promise<Ingredient> {
        const response = await apiClient.patch(`/ingredients/${id}`, data);
        return response.data;
    }

    async delete(id: string): Promise<void> {
        await apiClient.delete(`/ingredients/${id}`);
    }

    async findById(id: string): Promise<Ingredient | null> {
        try {
            const response = await apiClient.get(`/ingredients/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }
}