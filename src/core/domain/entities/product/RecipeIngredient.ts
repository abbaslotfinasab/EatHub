// core/domain/entities/sales/RecipeIngredient.ts
// core/domain/entities/sales/RecipeIngredient.ts
import type {UnitType} from '../inventory/Ingredient';

export const ComponentType = {
    INGREDIENT: 'ingredient',
    MATERIAL: 'material',
} as const;

export type ComponentTypeType = typeof ComponentType[keyof typeof ComponentType];

export interface RecipeIngredient {
    id: string;
    recipeId: string;
    componentType: ComponentTypeType;   // 'ingredient' یا 'material'
    componentId: string;                // شناسه Ingredient یا Material
    quantity: number;
    unit: UnitType;                     // واحد مصرف (اختیاری، می‌تواند از واحد ماده اصلی متفاوت باشد)
    substituteComponentId?: string | null; // جایگزین (با همان نوع مؤلفه)
    createdAt: string;
    updatedAt: string;
}

export interface RecipeIngredient {
    id: string;
    recipeId: string;               // ارجاع به Recipe
    componentType: ComponentTypeType;   // 'ingredient' یا 'material'
    ingredientId?: string;          // ارجاع به Ingredient (اختیاری)
    materialId?: string;            // ارجاع به Material (اختیاری)
    quantity: number;
    unit: UnitType;                 // واحد مصرف (می‌تواند با واحد اصلی متفاوت باشد)
    substituteIngredientId?: string | null;
    substituteMaterialId?: string | null;
    createdAt: string;
    updatedAt: string;
}