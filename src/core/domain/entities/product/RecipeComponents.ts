// core/domain/entities/sales/RecipeIngredient.ts

export const ComponentType = {
    INGREDIENT: 'ingredient',
    MATERIAL: 'material',
} as const;

export type ComponentType = typeof ComponentType[keyof typeof ComponentType];


export interface RecipeComponents {
    id?: string;
    recipeId?:string
    componentType?: ComponentType;   // 'ingredient' یا 'material'
    ingredientId?: string | null | undefined;          // ارجاع به Ingredient (اختیاری)
    materialId?: string | null | undefined;            // ارجاع به Material (اختیاری)
    quantity: number;
    substituteIngredientId?: string | null;
    substituteMaterialId?: string | null;
    createdAt?: string;
    updatedAt?: string;
}