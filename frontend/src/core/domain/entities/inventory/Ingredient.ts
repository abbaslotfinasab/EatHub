export const Unit = {
    KG: 'kg',
    G: 'g',
    L: 'l',
    ML: 'ml',
    PIECE: 'pc',
    PACK: 'pk',
} as const;

export type UnitType = typeof Unit[keyof typeof Unit];
export type PreparationLevel = 'raw' | 'semi_prepared';

export interface Ingredient {
    id: string;
    name: string;
    sku: string | null;
    unit: UnitType;
    preparationLevel: PreparationLevel;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}

export interface IngredientInput {
    name: string;
    sku?: string | null;
    unit: UnitType;
    preparationLevel?: PreparationLevel;
    isActive?: boolean;
}

export interface IngredientPage {
    count: number;
    page: number;
    pageSize: number;
    results: Ingredient[];
}
