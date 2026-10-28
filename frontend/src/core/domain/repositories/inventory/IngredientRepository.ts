import type { Ingredient, IngredientInput, IngredientPage, PreparationLevel, UnitType } from '../../entities/inventory/Ingredient.ts';

export interface IngredientFilters {
    page?: number;
    pageSize?: number;
    search?: string;
    isActive?: boolean;
    unit?: UnitType;
    preparationLevel?: PreparationLevel;
}

export interface IngredientRepository {
    create(ingredient: IngredientInput): Promise<Ingredient>;
    findById(id: string): Promise<Ingredient | null>;
    findByIds(ids: string[]): Promise<Ingredient[]>;
    findAll(filters?: IngredientFilters): Promise<IngredientPage>;
    update(id: string, data: Partial<IngredientInput>): Promise<Ingredient>;
    delete(id: string): Promise<void>;
}
