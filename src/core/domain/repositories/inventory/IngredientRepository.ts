// domain/repositories/IngredientRepository.ts
import type {Ingredient} from '../../entities/inventory/Ingredient.ts';

export interface IngredientRepository {
    create(ingredient: Omit<Ingredient, 'id'>): Promise<Ingredient>;
    findById(id: string): Promise<Ingredient | null>;
    findByIds(ids: string[]): Promise<Ingredient[]>; // 👈 اضافه شد
    findAll(filters?: IngredientFilters): Promise<Ingredient[]>;
    update(id: string, data: Partial<Ingredient>): Promise<Ingredient>;
    delete(id: string): Promise<void>;
}

export interface IngredientFilters {
    categoryId?: string;
    supplierId?: string;
    isActive?: boolean;
    lowStock?: boolean; // currentStock <= reorderLevel
    search?: string;
}