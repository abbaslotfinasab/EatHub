// domain/repositories/IngredientRepository.ts
import type {Category} from '../../entities/inventory/Category.ts';

export interface CategoryRepository {
    create(category: Omit<Category, 'id'>): Promise<Category>;
    findById(id: string): Promise<Category | null>;
    findAll(filters?: CategoryFilters): Promise<Category[]>;
    update(id: string, data: Partial<Category>): Promise<Category>;
    delete(id: string): Promise<void>;
}

export interface CategoryFilters {
    isActive?: boolean;
    search?: string;
    unit?: string;

}