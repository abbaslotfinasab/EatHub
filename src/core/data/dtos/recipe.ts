import type {Recipe} from "../../domain/entities/product/Recipe.ts";
import {ComponentType, type RecipeComponents} from "../../domain/entities/product/RecipeComponents.ts";

export const mockRecipes: Recipe[] = [
    {
        id: 'rec-1',
        name: 'سس مایونز خانگی',
        description: 'سس خامه‌ای لطیف',
        instructions: 'مواد را مخلوط کنید.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: 'rec-2',
        name: 'خمیر پیتزا',
        description: 'خمیر نرم و لطیف',
        instructions: 'آرد و مخمر و آب را مخلوط کنید.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
    {
        id: 'rec-3',
        name: 'سس قارچ مخصوص استیک',
        description: 'سس غلیظ و خوشمزه',
        instructions: 'قارچ و خامه را بپزید.',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    },
];

// داده‌های ساختگی برای مواد مصرفی هر رسپی
export const mockIngredients: Record<string, RecipeComponents[]> = {
    'rec-1': [
        {
            id: 'ing-1',
            recipeId: 'rec-1',
            componentType: ComponentType.INGREDIENT,
            ingredientId: 'ing-egg',
            materialId: undefined,
            quantity: 2,
            substituteIngredientId: null,
            substituteMaterialId: null,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        },
        {
            id: 'ing-2',
            recipeId: 'rec-1',
            componentType: ComponentType.INGREDIENT,
            ingredientId: 'ing-oil',
            materialId: undefined,
            quantity: 0.5,
            substituteIngredientId: null,
            substituteMaterialId: null,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        },
    ],
    'rec-2': [
        {
            id: 'ing-3',
            recipeId: 'rec-2',
            componentType: ComponentType.INGREDIENT,
            ingredientId: 'ing-flour',
            materialId: undefined,
            quantity: 500,
            substituteIngredientId: null,
            substituteMaterialId: null,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        },
    ],
    'rec-3': [], // بدون ماده
};